import requests
import argparse
import re
import unidecode
import urllib.parse
import csv
import sys

special_char_map = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss'}

ascii_art = r"""
   ,--,                                                                
,---.'|                                                                
|   | :               ,---,                           ____             
:   : |     ,--,    .'  .' `\                       ,'  , `.,-.----.   
|   ' :   ,--.'|  ,---.'     \          ,--,     ,-+-,.' _ |\    /  \  
;   ; '   |  |,   |   |  .`\  |       ,'_ /|  ,-+-. ;   , |||   :    | 
'   | |__ `--'_   :   : |  '  |  .--. |  | : ,--.'|'   |  |||   | .\ : 
|   | :.'|,' ,'|  |   ' '  ;  :,'_ /| :  . ||   |  ,', |  |,.   : |: | 
'   :    ;'  | |  '   | ;  .  ||  ' | |  . .|   | /  | |--' |   |  \ : 
|   |  ./ |  | :  |   | :  |  '|  | ' |  | ||   : |  | ,    |   : .  | 
;   : ;   '  : |__'   : | /  ; :  | : ;  ; ||   : |  |/     :     |`-' 
|   ,/    |  | '.'|   | '` ,/  '  :  `--'   \   | |`-'      :   : :    
'---'     ;  :    ;   :  .'    :  ,      .-./   ;/          |   | :    
          |  ,   /|   ,.'       `--`----'   '---'           `---'.|    
           ---`-' '---'                                       `---`    
                                                                       
"""

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(ascii_art + "\nLinkedIn Employee Email Extractor by Iulian" + "\n")
        super().error(message)

def get_hunter_api_key(config_file='hunter.conf'):
    with open(config_file, 'r') as f:
        for line in f:
            if line.strip().startswith('hunter_api'):
                return line.strip().split('=', 1)[1].strip().strip('"').strip("'")
    raise ValueError("hunter_api key not found in hunter.conf")

def get_email_pattern(domain, hunter_api_key):
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={hunter_api_key}"
    resp = requests.get(url)
    data = resp.json()
    if 'data' in data and 'pattern' in data['data']:
        return data['data']['pattern']
    return None

def generate_email(firstname, lastname, pattern, domain):
    first = firstname.lower().replace(" ", "").translate(special_char_map)
    last = lastname.lower().replace(" ", "").translate(special_char_map)
    email = pattern.replace('{first}', first).replace('{last}', last)
    email = email.replace('{f}', first[0] if first else '').replace('{l}', last[0] if last else '')
    if '@' not in email:
        email += f'@{domain}'
    return email

def clean_data(data):
    emoj = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
                      "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
                      "\U00002500-\U00002BEF\U00002702-\U000027B0"
                      "\U000024C2-\U0001F251\U0001f926-\U0001f937"
                      "\U00010000-\U0010ffff\u2640-\u2642\u2600-\u2B55"
                      "\u200d\u23cf\u23e9\u231a\ufe0f\u3030]+", re.UNICODE)
    cleaned = re.sub(emoj, '', data).strip()
    cleaned = cleaned.replace('Ü','Ue').replace('Ä','Ae').replace('Ö','Oe').replace('ü','ue').replace('ä','ae').replace('ö','oe')
    cleaned = cleaned.replace(',', '').replace(';', ',')
    cleaned = unidecode.unidecode(cleaned)
    return cleaned.strip()

def get_company_id(company, headers, cookies):
    company_encoded = urllib.parse.quote(company)
    api1 = f"https://www.linkedin.com/voyager/api/voyagerOrganizationDashCompanies?decorationId=com.linkedin.voyager.dash.deco.organization.MiniCompany-10&q=universalName&universalName={company_encoded}"
    r = requests.get(api1, headers=headers, cookies=cookies, timeout=200)
    r.raise_for_status()
    return r.json()["elements"][0]["entityUrn"].split(":")[-1]

def get_employee_data(company_id, start, headers, cookies, count=10):
    api2 = f"https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-165&origin=COMPANY_PAGE_CANNED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List({company_id}),resultType:List(PEOPLE)),includeFiltersInResponse:false)&count={count}&start={start}"
    r = requests.get(api2, headers=headers, cookies=cookies, timeout=200)
    r.raise_for_status()
    return r.json()

def parse_employee_results(results):
    employee_dict = []
    for employee in results:
        try:
            account_name = clean_data(employee["itemUnion"]['entityResult']["title"]["text"]).split(" ")
            badwords = ['Prof.', 'Dr.', 'M.A.', ',', 'LL.M.']
            for word in list(account_name):
                if word in badwords:
                    account_name.remove(word)
            firstname = ' '.join(account_name[:-1]) if len(account_name) > 2 else account_name[0]
            lastname = account_name[-1]
        except:
            continue
        try:
            position = clean_data(employee["itemUnion"]['entityResult']["primarySubtitle"]["text"])
        except:
            position = "N/A"
        employee_dict.append({
            "firstname": firstname,
            "lastname": lastname,
            "position": position
        })
    return employee_dict

def get_email_firstname(firstname):
    # Only use the first word before space or hyphen
    return re.split(r'[\s\-]', firstname)[0]

def main():
    parser = CustomArgumentParser(
        description=ascii_art + "\nLinkedIn Employee Email Extractor by Iulian",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--url", required=True, help="LinkedIn company url - https://www.linkedin.com/company/<company>")
    parser.add_argument("--cookie", required=True, help="LinkedIn 'li_at' session cookie")
    parser.add_argument("--domain", required=True, help="Company email domain (e.g. example.com)")
    parser.add_argument("--output-csv", required=False, help="CSV output file")
    args = parser.parse_args()

    if not args.url.startswith("https://www.linkedin.com/company/"):
        print("Invalid LinkedIn company URL.")
        return
    company = args.url.partition('company/')[2].split('/')[0]

    JSESSIONID = "ajax:5739908118104050450"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Content-type': 'application/json',
        'Csrf-Token': JSESSIONID
    }
    cookies = {"li_at": args.cookie, "JSESSIONID": JSESSIONID}

    hunter_api_key = get_hunter_api_key()
    email_pattern = get_email_pattern(args.domain, hunter_api_key)
    if not email_pattern:
        print(f"Could not determine email pattern for {args.domain} from Hunter.io")
        return
    print(f"Email pattern for {args.domain}: {email_pattern}")

    company_id = get_company_id(company, headers, cookies)

    # Get total number of employees
    first_page = get_employee_data(company_id, 0, headers, cookies)
    try:
        paging_total = first_page["paging"]["total"]
    except Exception:
        print("Could not determine total number of employees.")
        return

    employees = []
    for start in range(0, paging_total, 10):
        data = get_employee_data(company_id, start, headers, cookies)
        for i in range(3):
            try:
                results = data["elements"][i]["items"]
                employees.extend(parse_employee_results(results))
            except:
                pass

    seen = set()
    unique_employees = []
    for d in employees:
        dedupe_key = (d.get("firstname"), d.get("lastname"))
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            unique_employees.append(d)

    for person in unique_employees:
        email_firstname = get_email_firstname(person["firstname"]).replace(".", "").lower().translate(special_char_map)
        lastname_clean = person["lastname"].replace(".", "").lower().translate(special_char_map)
        person["email"] = generate_email(email_firstname, lastname_clean, email_pattern, args.domain)

    if args.output_csv:
        with open(args.output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Firstname", "Lastname", "Email", "Position"])
            for person in unique_employees:
                writer.writerow([person['firstname'], person['lastname'], person['email'], person['position']])
        print(f"Results written to {args.output_csv}")
    else:
        print("Firstname;Lastname;Email;Position")
        for person in unique_employees:
            print(f"{person['firstname']};{person['lastname']};{person['email']};{person['position']}")

if __name__ == "__main__":
    main()