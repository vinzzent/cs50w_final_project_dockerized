#!/bin/bash

set -o errexit
set -o nounset

celery -A pbi_manager worker -l INFO