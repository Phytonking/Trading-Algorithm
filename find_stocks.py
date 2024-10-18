import requests
import csv
from io import StringIO
import schedule
import time
from datetime import datetime, timedelta
import pytz

# URL for the CSV export
URL = "https://finviz.com/screener.ashx?o=tickersfilter&t=ABR%2CAKR%2CALHC%2CAM%2CAMBP%2CAPAM%2CATHM%2CAVA%2CBIPC%2CBKE%2CBSM%2CCATY%2CCNO%2CCRK%2CCUZ%2CCVI%2CDEI%2CDXC%2CEDR%2CEPR%2CFCPT%2CFFIN%2CFHB%2CFIZZ%2CGBCI%2CHIW%2CHMY%2CJHG%2CJWN%2CKMT%2CKNTK%2CKRC%2CKSS%2CLNC%2CLU%2CMAC%2CMDU%2CNNN%2CNSA%2COUT%2CPSEC%2CROIC%2CSFNC%2CSHOO%2CSKT%2CTRN%2CUE%2CVFC%2CVIRT%2CVNO"

def find_stocks(limit=None):
    try:
        # Fetch the CSV content
        response = requests.get(URL)
        response.raise_for_status()  # Raise an exception for bad responses
        
        # Read the CSV content
        csv_content = StringIO(response.text)
        csv_reader = csv.DictReader(csv_content)
        
        # Initialize ticker1
        ticker1 = None
        
        # Print the tickers
        print("Tickers:")
        for index, row in enumerate(csv_reader):
            if limit is not None and index >= limit:
                break
            print(row['Ticker'])
            if index == 0:
                ticker1 = row['Ticker']
        
        # Print ticker1
        if ticker1:
            print(f"\nFirst ticker (ticker1): {ticker1}")
            return True  # Return True if a ticker was found
        else:
            print("\nNo tickers found.")
            return False  # Return False if no ticker was found
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
    except KeyError:
        print("Error: 'Ticker' column not found in the CSV")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return False  # Return False if any exception occurred

def job():
    print(f"Running job at {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    if find_stocks(limit=1):
        return schedule.CancelJob  # Cancel the job if a ticker was found

def main():
    # Set the start time to 9:30 EST
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    start_time = now
    
    # If it's already past 9:35 EST today, schedule for tomorrow
    if now > start_time:
        start_time += timedelta(seconds=1)
    
    # Calculate the delay until the start time
    delay = (start_time - now).total_seconds()
    
    print(f"Waiting until {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')} to start the algo...")
    
    # Sleep until the start time
    time.sleep(1)
    
    # Schedule the job to run every minute
    schedule.every(1).minutes.do(job)
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()