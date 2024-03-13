# -*- coding: utf-8 -*-
import argparse

from acestream_search.common.constants import CATEGORIES
from acestream_search.events import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--category',
        type=str,
        choices=CATEGORIES.keys(),
        default=None,
        help='Event category (default: all)'
    )
    parser.add_argument(
        '--search',
        type=str,
        default='',
        metavar='TEXT',
        help='Text to look for in the event titles (default: any text)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=1,
        help='Events starting within the next number of hours. '
        'Started events are also included (2 hours ago max). '
        '(default: 1 hour)'
    )
    parser.add_argument(
        '--show-empty',
        action='store_true',
        default=False,
        help='Show events with no available acestream links (default: False)'
    )
    args = parser.parse_args()
    run(args.category, args.search, args.hours, args.show_empty)


if __name__ == '__main__':
    main()
