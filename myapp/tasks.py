from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def scrape_market_data():
    """
    Task to scrape NEPSE market data.
    Runs every minute during market hours.
    """
    logger.info("Starting market data scrape task")
    try:
        # Run the existing scraper command which now uses StockService
        call_command('scrape_nepse', once=True)
        logger.info("Market data scrape task completed successfully")
    except Exception as e:
        logger.error(f"Error in market data scrape task: {str(e)}")

@shared_task
def sync_stock_metadata():
    """
    Task to sync stock metadata (symbols, names, sectors).
    Runs daily.
    """
    logger.info("Starting stock metadata sync task")
    try:
        call_command('sync_metadata')
        logger.info("Stock metadata sync task completed successfully")
    except Exception as e:
        logger.error(f"Error in stock metadata sync task: {str(e)}")

@shared_task
def generate_watchlist_recommendations():
    """
    Task to generate stock recommendations for watchlist items.
    Runs daily at 3:00 PM.
    """
    logger.info("Starting watchlist recommendation task")
    try:
        # Run the recommendation engine for watchlist only
        call_command('run_recommendations', watchlist_only=True)
        logger.info("Watchlist recommendation task completed successfully")
    except Exception as e:
        logger.error(f"Error in watchlist recommendation task: {str(e)}")
