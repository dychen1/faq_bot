from dataclasses import dataclass
from logging import Logger

import sqlglot
from sqlglot import expressions as exp
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class SQLValidationResult:
    """Result of SQL validation operation."""

    is_valid: bool
    message: str
    validated_query: str | None = None


def validate_and_limit_sql(
    query: str,
    dialect: str,
    logger: Logger,
    allowed_tables: set[str] | None = None,
    max_limit: int = 100,
) -> SQLValidationResult:
    """
    Validate SQL query to ensure it's a SELECT-only query with proper security constraints.

    Automatically adds LIMIT 100 if no limit is specified or if limit exceeds 100.
    Recursively validates all parts of the query including subqueries and CTEs.

    Args:
        query: SQL query string to validate
        allowed_tables: Set of allowed table names. If None, allows any table
        dialect: SQL dialect to use for parsing (postgres, mysql, sqlite, etc.)

    Returns:
        SQLValidationResult containing:
        - is_valid: Boolean indicating if query passed validation
        - message: Description of validation result or specific error
        - validated_query: Query with LIMIT applied, or None if validation failed

    Example:
        >>> result = validate_and_limit_sql("SELECT * FROM users WHERE age > 18")
        >>> if result.is_valid:
        ...     print(f"Safe query: {result.modified_query}")
    """
    try:
        # Parse the SQL query
        parsed = sqlglot.parse_one(query, dialect=dialect)
        logger.debug(f"Parsed query: {parsed}")

        # Check if it's a SELECT statement
        if not isinstance(parsed, exp.Select):
            return SQLValidationResult(False, "Only SELECT statements are allowed", None)

        # Validate table access if table whitelist is provided
        if allowed_tables is not None:
            table_validation = _validate_table_access(parsed, allowed_tables)
            if not table_validation.is_valid:
                return SQLValidationResult(False, table_validation.message, None)

        # Check and enforce LIMIT constraint
        validated_query = _add_limit(parsed, query, dialect, max_limit)
        logger.info(f"Validated query: {validated_query}")
        return SQLValidationResult(True, "Query validation passed", validated_query)

    except ParseError as e:
        return SQLValidationResult(False, f"SQL parsing error: {str(e)}", None)
    except Exception as e:
        return SQLValidationResult(False, f"Validation error: {str(e)}", None)


def _validate_table_access(node: exp.Expression, allowed_tables: set[str]) -> SQLValidationResult:
    """
    Validate that only whitelisted tables are being accessed.

    Checks all table references in the query including those in subqueries,
    JOINs, and CTEs against the provided whitelist.

    Args:
        node: SQLGlot expression node to validate
        allowed_tables: Set of allowed table names (case-insensitive)

    Returns:
        SQLValidationResult indicating if table access is valid
    """
    accessed_tables: set[str] = set()

    # Find all table references
    for table_node in node.find_all(exp.Table):
        table_name = table_node.name.lower()
        accessed_tables.add(table_name)

    # Check if all accessed tables are in the allowed list
    allowed_lower = {t.lower() for t in allowed_tables}
    disallowed_tables = accessed_tables - allowed_lower

    if disallowed_tables:
        return SQLValidationResult(False, f"Access to tables not allowed: {', '.join(sorted(disallowed_tables))}", None)

    return SQLValidationResult(True, "Table access validation passed", None)


def _add_limit(parsed: exp.Select, original_query: str, dialect: str, max_limit: int) -> str:
    """
    If no LIMIT exists, adds LIMIT with default value of 100.
    If LIMIT exists but exceeds 100, replaces it with LIMIT 100.
    Preserves existing limits ≤ 100.

    Args:
        parsed: Parsed SELECT statement
        original_query: Original query string
        dialect: SQL dialect for query generation
        max_limit: maximum limit value

    Returns:
        Modified query string with appropriate LIMIT clause
    """

    # Check if query already has a LIMIT clause
    existing_limit = parsed.args.get("limit")

    if existing_limit:
        # Extract the limit value
        if isinstance(existing_limit.expression, exp.Literal):
            try:
                limit_value = int(existing_limit.expression.this)
                if limit_value <= max_limit:
                    # Limit is acceptable, return original query
                    return original_query
                else:
                    # Replace with max_limit
                    existing_limit.expression = exp.Literal.number(str(max_limit))
            except (ValueError, TypeError):
                # Non-numeric limit, replace with max_limit
                existing_limit.expression = exp.Literal.number(str(max_limit))
        else:
            # Complex limit expression, replace with max_limit
            existing_limit.expression = exp.Literal.number(str(max_limit))
    else:
        # Add LIMIT clause
        parsed = parsed.limit(max_limit)

    return parsed.sql(dialect=dialect, pretty=True)


# TODO: Add complexity analysis and expensive operation detection to prevent resource-intensive queries
