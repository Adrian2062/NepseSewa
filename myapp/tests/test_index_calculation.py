from django.test import TestCase
from django.utils import timezone
from myapp.models import NEPSEIndex
from myapp.views import get_latest_nepse_index_with_change
from datetime import timedelta

class NEPSEIndexCalculationTest(TestCase):
    def setUp(self):
        # Create data for two different days
        self.yesterday = timezone.now() - timedelta(days=1)
        self.today = timezone.now()
        
        # Yesterday's close
        NEPSEIndex.objects.create(
            timestamp=self.yesterday,
            index_value=2000.0,
            percentage_change=1.0
        )
        
        # Today's value
        self.latest = NEPSEIndex.objects.create(
            timestamp=self.today,
            index_value=2100.0,
            percentage_change=0.0 # Simulated bad data from scraper
        )

    def test_calculation_with_previous_day(self):
        """Test that change is calculated correctly when previous day exists"""
        result = get_latest_nepse_index_with_change()
        
        # Expected change = ((2100 - 2000) / 2000) * 100 = 5.0%
        self.assertEqual(result['value'], 2100.0)
        self.assertEqual(result['change_pct'], 5.0)

    def test_calculation_without_previous_day(self):
        """Test fallback when no previous day data exists"""
        NEPSEIndex.objects.all().delete()
        
        # Create only one record
        NEPSEIndex.objects.create(
            timestamp=timezone.now(),
            index_value=2100.0,
            percentage_change=2.5
        )
        
        result = get_latest_nepse_index_with_change()
        self.assertEqual(result['change_pct'], 2.5)

    def test_calculation_zero_previous(self):
        """Test handling of zero/invalid previous value to avoid division by zero"""
        # This shouldn't happen with real NEPSE data but good to test or at least know behavior
        NEPSEIndex.objects.all().delete()
        
        NEPSEIndex.objects.create(
            timestamp=self.yesterday,
            index_value=0.0,
            percentage_change=0.0
        )
        NEPSEIndex.objects.create(
            timestamp=self.today,
            index_value=2100.0,
            percentage_change=0.0
        )
        
        result = get_latest_nepse_index_with_change()
        # Should fallback to 0.0 or the field value
        self.assertEqual(result['change_pct'], 0.0)
