#!/bin/sh
valgrind --tool=memcheck -v --leak-check=full --track-origins=yes ./flare >valgrind.txt 2>&1
