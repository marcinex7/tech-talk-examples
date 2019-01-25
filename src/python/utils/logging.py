import logging.config

import structlog


def init_logging():
    pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    logging.config.dictConfig({
        'version': 1,
        "disable_existing_loggers": True,
        'formatters': {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": pre_chain,
            },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            }
        },
        'loggers': {
            '': {
                'handlers': ['stdout'],
                'level': logging.INFO,
            },
            'gRPC_client': {
                'level': logging.DEBUG
            },
            'gRPC_server': {
                'level': logging.DEBUG
            }

        }
    })
    structlog.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        processors=[structlog.stdlib.filter_by_level] + pre_chain +
                   [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
    )
