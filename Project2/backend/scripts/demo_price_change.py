"""
Demo Script: Show Real Price Change Detection
This demonstrates the actual technical implementation
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pricing_scraper import PricingScraper, PriceChangeDetector
from loguru import logger


async def demo_price_scraping():
    """Demonstrate real price scraping"""
    print("=" * 60)
    print("🔍 REAL PRICE SCRAPER DEMO")
    print("=" * 60)
    print()
    
    # Initialize scraper
    scraper = PricingScraper()
    detector = PriceChangeDetector(scraper)
    
    # Step 1: Scrape current prices
    print("📊 Step 1: Scraping Current Prices from Cloud Providers")
    print("-" * 60)
    current_prices = await scraper.scrape_all_providers()
    
    for provider, prices in current_prices.items():
        print(f"\n{provider.upper()} Pricing:")
        for instance_type, price_per_hour in prices.items():
            price_per_month = price_per_hour * 730
            print(f"  {instance_type:20s} ${price_per_hour:.4f}/hr = ${price_per_month:.2f}/month")
    
    print("\n" + "=" * 60)
    print("💰 Step 2: Simulating Price Reduction (for demo)")
    print("-" * 60)
    
    # Step 2: Simulate a price reduction to demonstrate detection
    print("\nSimulating 15% price reduction on AWS m5.xlarge...")
    scraper.simulate_price_reduction('aws', 'm5.xlarge', 15.0)
    
    print("\n" + "=" * 60)
    print("🔍 Step 3: Detecting Price Changes")
    print("-" * 60)
    
    # Step 3: Detect the change
    changes = await detector.check_for_changes()
    
    if changes:
        print(f"\n✅ Detected {len(changes)} price change(s):\n")
        for change in changes:
            print(f"Provider: {change['provider'].upper()}")
            print(f"Instance Type: {change['instance_type']}")
            print(f"Old Price: ${change['old_price_per_hour']:.4f}/hr (${change['old_price_per_month']:.2f}/month)")
            print(f"New Price: ${change['new_price_per_hour']:.4f}/hr (${change['new_price_per_month']:.2f}/month)")
            print(f"Reduction: {change['reduction_pct']:.1f}%")
            print(f"Savings: ${change['savings_per_month']:.2f}/month")
            print(f"Detected At: {change['detected_at']}")
            print("-" * 60)
    else:
        print("\nℹ️ No price changes detected (this is normal if prices haven't changed)")
        print("   The scraper is working - it's comparing current vs historical prices")
    
    print("\n" + "=" * 60)
    print("📋 Technical Details:")
    print("-" * 60)
    print("""
How It Works Technically:

1. PRICE SCRAPING:
   - Uses real pricing data from cloud providers
   - AWS: Current EC2 pricing (real 2024 prices)
   - GCP: Current Compute Engine pricing
   - Azure: Current VM pricing
   - Stores in JSON file for persistence

2. PRICE HISTORY:
   - First run: Stores current prices as baseline
   - Subsequent runs: Compares current vs. historical
   - Detects changes >5% automatically

3. CHANGE DETECTION:
   - Compares price_per_hour for each instance type
   - Calculates percentage change
   - Flags reductions >5% as opportunities
   - Calculates monthly savings automatically

4. PERSISTENCE:
   - Price history stored in: /app/data/price_history.json
   - Survives container restarts
   - Can be reset by deleting the file

5. INTEGRATION:
   - Called by PriceMonitor service
   - Available via API: GET /api/cost/check-prices
   - Can be scheduled via N8N workflow
    """)
    
    print("=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_price_scraping())

