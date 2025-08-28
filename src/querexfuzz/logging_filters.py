# in querexfuzz/logging_filters.py
import logging


class OnlyParserFilter(logging.Filter):
    """Allows log records only from the 'querexfuzz.parser' logger."""

    def filter(self, record):
        return record.name.startswith('querexfuzz.parser')


class ExcludeParserFilter(logging.Filter):
    """Excludes log records from the 'querexfuzz.parser' logger."""

    def filter(self, record):
        return not record.name.startswith('querexfuzz.parser')


class OnlyParserDebugFilter(logging.Filter):
    """Allows log records only from 'querexfuzz.parser' AND at DEBUG level."""

    def filter(self, record):
        return (record.name.startswith('querexfuzz.parser')
                and record.levelno == logging.DEBUG)


class ExcludeParserDebugFilter(logging.Filter):
    """Excludes log records from 'querexfuzz.parser' at DEBUG level."""

    def filter(self, record):
        # This will be False only for parser debug messages, blocking them.
        # All other messages will pass (return True).
        return not (record.name.startswith('querexfuzz.parser')
                    and record.levelno == logging.DEBUG)
