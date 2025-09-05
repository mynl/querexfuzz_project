from logging import getLogger
from pathlib import Path
import pprint

from lark import Lark, Transformer, v_args

# Initialize the logger for this module
logger = getLogger(__name__)

# Path to the grammar file relative to this file
GRAMMAR_FILE = Path(__file__).parent / "grammar.lark"

# ==============================================================================
# The Lark instance is created ONCE when the module is imported.
_LARK_PARSER = Lark.open(GRAMMAR_FILE, start='query',
                         parser='earley', lexer='dynamic')
# ==============================================================================

logger.info('built parser.py')


@v_args(inline=True)
class QueryTransformer(Transformer):
    """Transforms the Lark parse tree into a structured dictionary."""

    def __init__(self):
        super().__init__()
        self.spec = {
            'select': {'include': [], 'exclude': []}, 'sort': [],
            'regex': [], 'where': None, 'top': 0, 'flags': [],
            'dates': [], 'fuzzy': None
        }
        logger.debug("QueryTransformer initialized with empty spec.")

    def empty(self):
        logger.debug("Parsing an empty query string.")
        return self.spec

    def query(self, clause_list):
        logger.debug(
            "Finalizing query transformation on list %s:", clause_list)
        return self.spec

    def clause_list(self, *clauses):
        logger.debug(
            "Assembling %s parsed clauses into final spec.", len(clauses))
        for clause_type, value in clauses:
            logger.debug("  -> Applying clause '%s' with value: %s",
                         clause_type, value)
            if clause_type == 'flags' or clause_type == 'regex' or clause_type == 'sort' or clause_type == 'dates':
                # allow multiple
                self.spec[clause_type].extend(value)
            # only single top, select , or where - see if anything there
            elif clause_type == 'top':
                if self.spec['top'] != -1:
                    logger.info('re-setting top from %s to %s',
                                self.spec['top'], value)
            elif self.spec.get(clause_type, []):
                # select and where are lists
                logger.info('clause type "%s" already exists with value %s, overwritten by %s',
                            clause_type, self.spec[clause_type], value)
            self.spec[clause_type] = value
        return self.spec

    def clause(self, item):
        logger.debug(
            'Clause (aggregator) with item %s (should be a tuple of (type, value))', item)
        return item

    # Clauses
    def top_clause(self, tb, n):
        value = n
        logger.debug("Raw top_clause, value: %s (tb=%s)", value, tb)
        if tb == 'bottom':
            value = -value
        logger.debug("Parsed top_clause, %s -> %s", tb, value)
        return 'top', value

    def flags(self, *flags):
        logger.debug("Parsed flags, values: %s", flags)
        return 'flags', list(flags)

    def regex_clause(self, items):
        logger.debug("Parsed regex_clause, values: %s", items)
        return 'regex', items

    # def where_clause(self, expr):
    #     logger.debug(f"Parsed where_clause, expression: '%s'", expr)
    #     return 'where', expr

    def order_by_clause(self, _, __, sort_list):
        # responding to order_by_clause: (ORDER | SORT) [BY] column_sort_list
        # because of optionality, order and by are passed
        logger.debug(
            "Parsed order_by_clause, first args %s, %s;  sort list: %s", _, __, sort_list)
        return 'sort', sort_list

    def date_clause(self, *items):
        logger.debug("Parsed date_clause, items: %s", items)
        return 'dates', list(items)

    def select_clause(self, select_list):
        logger.debug("Parsed select_clause, list: %s", select_list)
        return 'select', select_list

    # Clause Components
    def regexes(self, head, *tail):
        value = [head] + list(tail)
        logger.debug(
            "Constructed regex list: %s from head %s and tail %s", value, head, tail)
        return value

    # def regex_item(self, bang, ident):
    def regex_item(self, item):
        # need to avoid getting Tree at top level
        # value = bang or ident
        logger.debug("Constructed regex_item: %s", item)
        return item

    def regex_bang(self, regex):
        value = ('BANG', regex[1:-1] if regex.startswith('/') else regex)
        logger.debug("Constructed regex_bang item: %s", value)
        return value

    def regex_ident(self, ident, regex):
        value = (ident, regex[1:-1] if regex.startswith('/') else regex)
        logger.debug("Constructed regex_ident item: %s", value)
        return value

    # def where_clause_list(self, head, *tail):
    #     # Constructs the full 'where' clause string.
    #     # 'tail' is now a tuple of (operator, expression) pairs.
    #     # Example: (('and', 'price > 10'), ('or', 'stock > 0'))
    #     logger.info(
    #         "Constructing where_clause_list from head='%s' and tail=%s", head, tail
    #     )
    #     parts = [head]

    #     # Iterate through the list of (operator, expression) tuples
    #     for operator, expression in zip(tail[::2], tail[1::2]):
    #         parts.append(operator)
    #         parts.append(expression)

    #     # Join all the parts with spaces
    #     full_expression = ' '.join(parts)
    #     logger.info("\tjoined 'where' conditions: '%s'", full_expression)
    #     return full_expression
# --- In your QueryTransformer class ---

# REMOVE the old where_clause_list method.
# ADD these new methods:
    def where_clause(self, _, expr):
        # This now receives the WHERE token, which we ignore.
        logger.debug("Parsed where_clause, expression: '%s', (_=%s)", expr, _)
        return 'where', expr

    def where_expression(self, head, *tail):
        """
        Constructs a query string from a head term and a tail of
        alternating operators and terms.
        """
        logger.debug(
            "Constructing where_expression from head='%s' and tail=%s", head, tail
        )
        parts = [head]

        # Use the zip method to process the flat tail into pairs
        for operator, expression in zip(tail[::2], tail[1::2]):
            parts.append(operator)
            parts.append(expression)

        full_expression = ' '.join(parts)
        logger.debug("\t-->joined where_expression: '%s'", full_expression)
        return full_expression

    def where_term(self, term):
        # This method just passes the result up the tree.
        logger.debug("Processing where_term, value: %s", term)
        return term

    def parenthesized_expression(self, inner_expr):
        """
        Receives the fully resolved expression from inside a pair of parentheses
        and wraps it in parentheses for the final output string.
        """
        # 'inner_expr' is the already-processed string from the recursive
        # call to the 'where_expression' method.
        result = f"({inner_expr})"
        logger.debug("Wrapping parenthesized expression: %s", result)
        return result

# end new; where item unchanged
    def where_item(self, ident, op, val):
        value = f"{ident} {op} {val}"
        logger.debug('Constructed where_item: "%s" '
                     '(from %s, %s, and %s)', value, ident, op, val)
        return value

    def column_sort_list(self, head, *tail):
        # logger.debug("column sort list with args head %s and tail %s, type %s", head, tail, type(tail))
        value = [head] + list(tail)
        logger.debug("Constructed column_sort_list: %s", value)
        return value

    def column_sort_item(self, item):
        logger.debug("Processing column_sort_item with item: %s", item)
        return item

    def column_sort_asc(self, ident):
        logger.debug(f"Parsed ascending sort for column: '{ident}'")
        return ident, True

    def column_sort_desc(self, ident):
        logger.debug(f"Parsed descending sort for column: '{ident}'")
        return ident, False

    def select_list(self, head_item, *rest_items):
        # Combine the first item with the tuple of the rest into one list
        all_items = [head_item] + list(rest_items)
        logger.debug("Constructing select list from all items: %s", all_items)
        inc, exc = [], []
        for item_type, value in all_items:
            if item_type == 'include':
                inc.append(value)
            elif item_type == 'exclude':
                exc.append(value)
            elif item_type == 'all':
                inc.append('*')
        result = {'include': inc, 'exclude': exc}
        logger.debug("Constructed select_list: %s", result)
        return result

    def select_item(self, item):
        logger.debug("Processing select_item with item: %s", item)
        return item

    def select_include_identifier(self, ident):
        logger.debug("Parsed select include: '%s'", ident)
        return 'include', ident

    def select_exclude_identifier(self, ident):
        logger.debug("Parsed select exclude: '%s'", ident)
        return 'exclude', ident

    def select_all(self):
        logger.debug("Parsed select all ('**')")
        return 'include', '__all__'

    def select_base(self):
        logger.debug("Parsed select base ('**')")
        return 'include', '__base__'

    def date_item(self, *args):
        logger.debug('\tdate args %s', args)
        field, spec = (args[0], args[1]) if len(args) > 1 else (None, args[0])
        value = {'field': field, **spec}
        logger.debug("Constructed date_item: %s", value)
        return value

    def date_specifier(self, *args):
        logger.debug('\tdate specifier args %s', args)
        unit = args[0]
        if len(args) == 1:
            # just m, y, q etc., which means m-1, end = 0
            value = {'unit': unit, 'start': 1, 'end': 0}
        elif len(args) == 2:
            value = {'unit': unit, 'start': args[1], 'end': '0'}
        else:
            value = {'unit': unit, 'start': args[1], 'end': args[2]}
        logger.debug("Constructed date_specifier: %s", value)
        return value

    def integer(self, n):
        value = int(n)
        logger.debug(
            "Processing integer, value: %s (original type: %s)", value, type(n))
        return value

    def number(self, n):
        # The INT and FLOAT terminals automatically convert the token's value,
        # so 'n' is already a Python int or float. This method just passes it up.
        logger.debug(
            "Processing (signed) number, value: %s (type: %s)", n, type(n))
        return n

    # Terminals
    def __default_token__(self, token):
        logger.debug("Processing TOKEN, type: %s, value: %s",
                     token.type, repr(token.value))
        return token.value


def parser(text: str) -> dict:
    """Parses a querexfuzz query string into a specification dictionary."""
    # logger.info('running parser on %s', text)
    logger.debug("""
*** Starting new parse job for query ***

   |
>>>| %s
   |
""", text)
    fuzzy_query = None
    if '#' in text:
        main_query, fuzzy_query = text.split('#', 1)
        logger.debug("Split query into main='%s' and fuzzy='%s'",
                     main_query, fuzzy_query)
    else:
        main_query = text.strip()
        logger.debug("No fuzzy query found. Main query: '%s'", main_query)

    try:
        logger.debug("Calling Lark to parse the main query...")
        tree = _LARK_PARSER.parse(main_query)
        logger.debug("Lark produced parse tree:\n%s", tree.pretty())
    except Exception as e:
        logger.error(f"Failed to parse query: '{main_query}.\n"
                     f"Error: {e}", exc_info=False)
        raise ValueError(f"Failed to parse query: '{main_query}'. Error {e}")

    try:
        logger.debug("Calling QueryTransformer to transform the tree...")
        transformer = QueryTransformer()
        spec = transformer.transform(tree)
    except Exception as e:
        logger.error(f"Failed to Transform: '{main_query}'.\n"
                     f"Error:\n{e}", exc_info=False)
        raise ValueError(f"Failed to transform query: '{main_query}'."
                         f" Error: {e}")

    try:
        spec['fuzzy'] = fuzzy_query.strip() if fuzzy_query else None
        # TODO: Get rid of this in prod!
        pretty_spec = pprint.pformat(spec, indent=2)
        logger.debug("Spec dictionary constructed: %s", pretty_spec)
        return spec
    except Exception as e:
        logger.error(f"Failed to print (unlikely) query: '{main_query}'. "
                     f"Error: {e}", exc_info=False)
        raise ValueError(f"Failed to finalize query: '{main_query}'. "
                         f"Error: {e}")
