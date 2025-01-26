from bs4 import BeautifulSoup as bs
import pandas as pd
import time
import datetime
import os
from tqdm import trange

import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ForumsScraper():
    def __init__(self):
        # Define emptry placeholders
        self.profile_list = []

        # Define the scope for the APIs
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Path to your service account JSON key file
        SERVICE_ACCOUNT_FILE = '/home/chris/credentials/thematic-gift-277111-1a38f1cdb4c7.json'

        # Authenticate and initialize the client
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        self.google_client = gspread.authorize(credentials)

        # Get Chrome driver info
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # if os.name == 'posix':
        #     chrome_path = '/home/chris/.wdm/drivers/chromedriver/linux64/131.0.6778.204/chromedriver-linux64/chromedriver'  
        # else:
        #     chrome_path = 'C:\\Users\\u783542\\.wdm\\drivers\\chromedriver\\win64\\131.0.6778.85\\chromedriver-win32\\chromedriver.exe'

        # self.chrome_driver = webdriver.Chrome(service=Service(chrome_path,
        #                                                         options=options))
        
        self.chrome_driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )       
        

    def get_gsheet(self, url, sheet=0):
        workbook = self.google_client.open_by_url(url)
        # # Access a specific worksheet
        worksheet_object = workbook.get_worksheet(sheet)

        return worksheet_object

    def tableau_login(self):
        url = "https://community.tableau.com/s"
        self.chrome_driver.get(url)

        try:
            elem = WebDriverWait(self.chrome_driver, 10).until(EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))) 
            if elem:
                cookies = self.chrome_driver.find_element(By.ID,"onetrust-accept-btn-handler")
                cookies.click()
                print("Cookie button clicked")
        except:
            print("Cookie button not found")
        time.sleep(10)

        elem = WebDriverWait(self.chrome_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'linkLabel'))) 

        if elem:
            login = self.chrome_driver.find_element(By.CLASS_NAME, 'linkLabel')
            login.click()
            print("Clicked Login")
        else:
            print("Menu button not found") 

        elem = WebDriverWait(self.chrome_driver, 30).until(EC.presence_of_element_located((By.ID, 'email'))) 

        email = self.chrome_driver.find_element(By.ID,"email")
        email.send_keys("chris@geatch.com")

        pwd = self.chrome_driver.find_element(By.ID,"password")
        pwd.send_keys("?8t@FdtXyfGX")

        btn = self.chrome_driver.find_element(By.ID,"signInButton")
        btn.click()

        time.sleep(15)

    def get_ambassadors(self):
        
        url = "https://www.tableau.com/community/community-leaders/ambassadors#community-forum"
        self.chrome_driver.get(url)

        WebDriverWait(self.chrome_driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'teaser-item__description'))) 
        soup = bs(self.chrome_driver.page_source) 

        sections = soup.find_all("article", class_='content')

        for section in sections:
            header = section.find("div",class_='text--centered')
            if header and 'Forum' in header.text:
                ambos = [x["href"].strip() for x in section.find_all("a", href=True) if "community.tableau.com/s/profile" in x["href"]]        

        ambos = list(set([x[:55] for x in ambos]))

        self.profile_list += [(x, "Ambassador") for x in ambos]
        self.profile_list = list(set(self.profile_list))

    
    def get_top150(self):
        urls_sheet = self.get_gsheet('https://docs.google.com/spreadsheets/d/1H86_fj8z8yBNKOZOIBGrxc8-hTc03XZxNxYBzTneo7w/edit',
                               1)
        urls = pd.DataFrame(urls_sheet.get_all_records())
        url_list = [(x,"Others") for x in list(urls["URL"].values)]
        self.profile_list += url_list

        self.profile_list = list(set(self.profile_list))


    def get_profile(self, url, role):
        self.chrome_driver.get(url)
        time.sleep(4)
        rep_panel = None
        try:        
            rep_panel = WebDriverWait(self.chrome_driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'reputationPoints')))
        except:
            print("Failed rep panel:", url)
            return None
        
        soup = bs(self.chrome_driver.page_source) 
        user_dict = {}
        
        user_dict["id"] = url[url.rfind('/')+1:]  
        user_dict["points"] = int(soup.find(class_="reputationPoints").text.strip().replace("(","").replace(" points)","").replace(" point)","").replace(',',''))
        statDescs = [x.text for x in soup.find_all(class_="statDesc")]
        statNumbers = [x.text for x in soup.find_all(class_="statNumber")]
        statDict = dict(zip(statDescs,statNumbers))    
        user_dict.update(statDict)     

        return user_dict
    
    def run_process(self):
        print("Setting up and connecting")
        self.tableau_login()
        self.get_ambassadors()
        self.get_top150()

        # Get rid of duplicates, favrouing the Ambassador second part of the tuple for any duplicates
        self.profile_list = list({key: value for key, value in reversed(self.profile_list)}.items())

        profiles = []
        print("Retrieving all selected profiles")
        for x in trange(len(self.profile_list)):
        # for profile_url, profile_type in self.profile_list:
            prof_dict = self.get_profile(self.profile_list[x][0], self.profile_list[x][1])
            profiles.append(prof_dict)

        print("Converting data to DataFrame")
        df = pd.DataFrame(profiles)
        # Replace Johan DeGroots ID
        df["id"] = df["id"].replace("0054T000001NkSe","XX54T000001NkSe")
        df["snapshot"] = datetime.datetime.now().date()

        print("Getting existing snapshots from Google Sheets")
        snapshot_sheet = self.get_gsheet('https://docs.google.com/spreadsheets/d/1H86_fj8z8yBNKOZOIBGrxc8-hTc03XZxNxYBzTneo7w/edit',
                    0)
        snapshot_data = pd.DataFrame(snapshot_sheet.get_all_records())
        # Ensure the `snapshot` column in the Google Sheets data is also in `date` format
        snapshot_data["snapshot"] = pd.to_datetime(snapshot_data["snapshot"]).dt.date

        print("Concatenating new snapshot with existing data")
        df_new = pd.concat([df,snapshot_data])
        df_new["snapshot"] = pd.to_datetime(df_new["snapshot"]).dt.date
        df_new = df_new.sort_values(by=["id","snapshot","points"]).drop_duplicates(subset=["id","snapshot"],keep="last")
        # print(df_new)
        for col in ["Following","Followers","Posts","Comments","Likes Received"]:
            df_new[col] = pd.to_numeric(df_new[col], errors='coerce').fillna(0).astype(int)
        df_new = df_new.sort_values(by=["id","snapshot"]).set_index(["id","snapshot"])

        print("Creating multi-index in new data")
        start_date = datetime.datetime(year=2023, month=4, day=21)
        all_dates = pd.date_range(start_date, datetime.datetime.now().date(), freq='D')
        new_index = pd.MultiIndex.from_product([df_new.index.levels[0],all_dates],names=["id","snapshot"])
        new_df = pd.DataFrame(index=new_index)
        
        df_new = new_df.merge(df_new,left_index=True,right_index=True,how='left').reset_index()
        # print(df_new.head())
        # print(df_new.info())
        df_new["points"] = df_new["points"].apply(lambda x: int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else None)

        print("Interpolating values for any missing dates")
        df_list = []

        for idx in df_new.id.unique():
            dft = df_new[df_new["id"] == idx].copy()  # Create a copy to avoid SettingWithCopyWarning
            for col in dft.columns:
                if col in ["points", "Following", "Followers", "Comments", "Likes Received", "Posts"]:
                    dft.loc[:, col] = dft[col].interpolate(method="linear", limit_area="inside")
                else:
                    dft.loc[:, col] = dft[col].bfill()  # Use bfill directly instead of fillna
            df_list.append(dft)

        df_new = pd.concat(df_list)

        print("Final tidying up")
        # Alter Johan De Groot's ID
        df_new["id"] = df_new["id"].replace("0054T000001NkSe","XX54T000001NkSe")
        df_new = df_new[[x for x in df_new.columns if "Unnamed" not in x]]

        print("Writing new DataFrame back to Google Sheets")
        snapshot_sheet.clear()
        set_with_dataframe(snapshot_sheet,df_new)

        self.chrome_driver.close()        
