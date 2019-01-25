# Copyright 2019 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_library(
  sources=['grpcio.py', 'grpcio_prep.py', 'register.py'],
  dependencies = [
    '3rdparty/python:future',
    'src/python/pants/backend/python/targets',
    'src/python/pants/build_graph',
    'src/python/pants/task',
    '3rdparty/python:pex',
    'src/python/pants/backend/python:plugin',
    'src/python/pants/backend/python/subsystems',
    'src/python/pants/base:workunit',
    'src/python/pants/base:build_environment',
    'src/python/pants/base:exceptions',
    'src/python/pants/subsystem',
    'src/python/pants/util:contextutil',
  ],
)