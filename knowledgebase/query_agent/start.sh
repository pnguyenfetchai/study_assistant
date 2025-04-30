#!/bin/bash

# Start the cron daemon
cron

# Start the query agent
python rag.py
