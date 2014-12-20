#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

if __name__ == '__main__':
    # We want to hook the logging before importing other modules which might already use log statements:
    from log import hook_logging
    hook_logging()

    import server
    server.start()