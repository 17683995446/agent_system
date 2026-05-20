#!/usr/bin/env python3
"""运行Phase 22 - 为了演示目的，运行30轮而不是100轮"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from phase22_extreme_endurance_test import Phase22ExtremeEnduranceTest

if __name__ == "__main__":
    # 运行30轮超高强度测试
    test = Phase22ExtremeEnduranceTest(total_iterations=30)
    test.run_all_tests()
