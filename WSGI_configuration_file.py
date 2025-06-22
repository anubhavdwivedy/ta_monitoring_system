import sys
import os
path = '/home/yourusername/ta_monitoring_system'  # Replace with your path
if path not in sys.path:
    sys.path.append(path)

from app import app as application
