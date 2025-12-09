"""
Farmtech Tests Package

This package contains all unit tests for the farmtech application views:
- test_auth_views.py: Tests for Keycloak authentication views
- test_dashboard_views.py: Tests for dashboard publishing views
- test_dataset_views.py: Tests for dataset update and template views
- test_group_views.py: Tests for group join request and listing views
- test_inference_views.py: Tests for inference/ML SSH command views
- test_queues_views.py: Tests for Celery queue monitoring views
"""

from farmtech.tests.test_auth_views import *
from farmtech.tests.test_dashboard_views import *
from farmtech.tests.test_dataset_views import *
from farmtech.tests.test_group_views import *
from farmtech.tests.test_inference_views import *
from farmtech.tests.test_queues_views import *
