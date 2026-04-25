# 美国大使馆和领事馆·自动预约

项目通过本地 `config.json` 读取参数, 支持:

- 查询可预约日期
- 按规则自动选择预约日期和时间
- 自动预约并保存预约信息

## 免责声明

本项目仅用于学习、测试
请勿将本项目用于任何违法违规或其他非常规用途, 使用者需自行承担由此产生的一切责任

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps
```

## 运行

```bash
python main.py
```

## 完整配置

```json
{
  "city": "BEIJING",
  "months": ["+0", "+1"],
  "service_index": 1,
  "show_browser": false,
  "timeout_seconds": 30,
  "check_once_max_seconds": 180,
  "interval_minutes": 0,
  "booking": {
    "enabled": false,
    "date_selection": {
      "targets": [],
      "filter_mode": "none",
      "weights": [],
      "final_pick": "earliest"
    },
    "time_selection": {
      "filter_mode": "none",
      "final_pick": "latest"
    },
    "applicant": {
      "last_name": "SAN",
      "first_name": "TAN",
      "date_of_birth": "2000-01-01",
      "telephone": "12345678",
      "email": "example@example.com",
      "citizenship": "SINGAPORE",
      "birth_country": "SINGAPORE",
      "sex": "M",
      "passport_number": "E12345678",
      "non_applicant_names": [
        "WANG WU",
        "WANG LU",
        "WANG ZU"
      ]
    },
    "bubble": {
      "enabled": false,
      "password": "XXXXXXXXXX"
    }
  }
}
```

## 查询预约配置

- `city`: 城市, 参考[缓存文件](cache/city.md)或下面列表
  <details><summary><code>City</code></summary>

  | Index | Country | City | Code |
  | -------- | -------- | -------- | -------- |
  | 1 | AFGHANISTAN | KABUL | KBL |
  | 2 | ALBANIA | TIRANA | TIA |
  | 3 | ALGERIA | ALGIERS | ALG |
  | 4 | ANGOLA | LUANDA | LUA |
  | 5 | ARGENTINA | BUENOS AIRES | BNS |
  | 6 | ARMENIA | YEREVAN | YRV |
  | 7 | AUSTRALIA | MELBOURNE | MLB |
  | 8 | AUSTRALIA | PERTH | PRT |
  | 9 | AUSTRALIA | SYDNEY | SYD |
  | 10 | AUSTRIA | VIENNA | VNN |
  | 11 | AZERBAIJAN | BAKU | BKU |
  | 12 | BAHAMAS | NASSAU | NSS |
  | 13 | BAHAMAS | NASSAU Outreach | NS2 |
  | 14 | BAHRAIN | MANAMA | MNA |
  | 15 | BANGLADESH | DHAKA | DHK |
  | 16 | BARBADOS | BRIDGETOWN | BG2 |
  | 17 | BELARUS | MINSK | MSK |
  | 18 | BELGIUM | BRUSSELS | BRS |
  | 19 | BELIZE | BELIZE | BLZ |
  | 20 | BENIN | COTONOU | COT |
  | 21 | BERMUDA | HAMILTON | HML |
  | 22 | BOLIVIA | LA PAZ | LPZ |
  | 23 | BOSNIA-HERZEGOVINA | SARAJEVO | SAR |
  | 24 | BOTSWANA | GABORONE | GAB |
  | 25 | BRAZIL | PORTO ALEGRE | PTA |
  | 26 | BRAZIL | BRASILIA | BRA |
  | 27 | BRAZIL | RECIFE | RCF |
  | 28 | BRAZIL | RIO DE JANEIRO | RDJ |
  | 29 | BRAZIL | SAO PAULO | SPL |
  | 30 | BRUNEI | BANDAR SERI BEGAWAN | BSB |
  | 31 | BULGARIA | SOFIA | SOF |
  | 32 | BURKINA FASO | OUAGADOUGOU | OUG |
  | 33 | BURMA | RANGOON | RNG |
  | 34 | BURUNDI | BUJUMBURA | BUJ |
  | 35 | CABO VERDE | PRAIA | PIA |
  | 36 | CAMBODIA | PHNOM PENH | PHP |
  | 37 | CAMEROON | YAOUNDE | YDE |
  | 38 | CANADA | CALGARY | CLG |
  | 39 | CANADA | HALIFAX | HLF |
  | 40 | CANADA | MONTREAL | MTL |
  | 41 | CANADA | OTTAWA | OTT |
  | 42 | CANADA | QUEBEC CITY | QBC |
  | 43 | CANADA | TORONTO | TRT |
  | 44 | CANADA | VANCOUVER | VAC |
  | 45 | CANADA | WINNIPEG | WNN |
  | 46 | CHAD | NDJAMENA | NDJ |
  | 47 | CHILE | SANTIAGO | SNT |
  | 48 | CHINA - MAINLAND | BEIJING | BEJ |
  | 49 | CHINA - MAINLAND | GUANGZHOU | GUZ |
  | 50 | CHINA - MAINLAND | SHANGHAI | SHG |
  | 51 | CHINA - MAINLAND | SHENYANG | SNY |
  | 52 | CHINA - MAINLAND | WUHAN | WUH |
  | 53 | COLOMBIA | BARRANQUILLA | BRR |
  | 54 | CONGO (BRAZZAVILLE) | BRAZZAVILLE | BRZ |
  | 55 | CONGO (KINSHASA) | KINSHASA | KIN |
  | 56 | COSTA RICA | SAN JOSE | SNJ |
  | 57 | COTE D`IVOIRE | ABIDJAN | ABJ |
  | 58 | CROATIA | ZAGREB | ZGB |
  | 59 | CUBA | HAVANA | HAV |
  | 60 | CURACAO | CURACAO | CRC |
  | 61 | CYPRUS | NICOSIA | NCS |
  | 62 | CZECH REPUBLIC | PRAGUE | PRG |
  | 63 | DENMARK | COPENHAGEN | CPN |
  | 64 | DJIBOUTI | DJIBOUTI | DJI |
  | 65 | DOMINICAN REPUBLIC | SANTO DOMINGO | SDO |
  | 66 | ECUADOR | QUITO | QTO |
  | 67 | EGYPT | CAIRO | CRO |
  | 68 | EQUATORIAL GUINEA | MALABO | MBO |
  | 69 | ERITREA | ASMARA | ASM |
  | 70 | ESTONIA | TALLINN | TAL |
  | 71 | ESWATINI | MBABANE | MBA |
  | 72 | ETHIOPIA | ADDIS ABABA | ADD |
  | 73 | FEDERATED STATES OF MICRONESIA | KOLONIA | KOL |
  | 74 | FIJI | SUVA | SUV |
  | 75 | FINLAND | HELSINKI | HLS |
  | 76 | FRANCE | BORDEAUX | BD1 |
  | 77 | FRANCE | LILLE | LL1 |
  | 78 | FRANCE | LYON | LN1 |
  | 79 | FRANCE | MARSEILLE | MRL |
  | 80 | FRANCE | NANTES | NN1 |
  | 81 | FRANCE | PARIS | PRS |
  | 82 | FRANCE | PARIS (U.S. Embassy Employees ONLY) | PS2 |
  | 83 | FRANCE | RENNES | RN1 |
  | 84 | FRANCE | STRASBOURG | STR |
  | 85 | GABON | LIBREVILLE | LIB |
  | 86 | GEORGIA | TBILISI | TBL |
  | 87 | GERMANY | BERLIN | BRL |
  | 88 | GERMANY | FRANKFURT | FRN |
  | 89 | GHANA | ACCRA | ACC |
  | 90 | GREAT BRITAIN AND NORTHERN IRELAND | EDINBURGH | EDN |
  | 91 | GREAT BRITAIN AND NORTHERN IRELAND | LONDON | LND |
  | 92 | GREECE | ATHENS | ATH |
  | 93 | GREECE | THESSALONIKI | TES |
  | 94 | GRENADA | ST GEORGES | SGE |
  | 95 | GUATEMALA | GUATEMALA CITY | GTM |
  | 96 | GUINEA | CONAKRY | CRY |
  | 97 | GUYANA | GEORGETOWN | GEO |
  | 98 | HAITI | PORT AU PRINCE | PTP |
  | 99 | HONDURAS | TEGUCIGALPA | TGG |
  | 100 | HONG KONG S. A. R. | HONG KONG | HNK |
  | 101 | HUNGARY | BUDAPEST | BDP |
  | 102 | ICELAND | REYKJAVIK | RKJ |
  | 103 | INDIA | CHENNAI ( MADRAS) | MDR |
  | 104 | INDIA | HYDERABAD | HYD |
  | 105 | INDIA | KOLKATA (CALCUTTA) | CLC |
  | 106 | INDIA | MUMBAI (BOMBAY) | BMB |
  | 107 | INDIA | NEW DELHI | NWD |
  | 108 | INDONESIA | DENPASAR (BALI) | DNP |
  | 109 | INDONESIA | JAKARTA | JAK |
  | 110 | INDONESIA | SURABAYA | SRB |
  | 111 | IRAQ | BAGHDAD | BGH |
  | 112 | IRAQ | ERBIL | ERB |
  | 113 | IRELAND | DUBLIN | DBL |
  | 114 | IRELAND | Outreach Appointment Schedule | DL2 |
  | 115 | ISRAEL | TEL AVIV | TLV |
  | 116 | ITALY | FLORENCE | FLR |
  | 117 | ITALY | GENOA | GEN |
  | 118 | ITALY | MILAN | MLN |
  | 119 | ITALY | NAPLES | NPL |
  | 120 | ITALY | ROME | RME |
  | 121 | JAMAICA | Kingston, Jamaica | KNG |
  | 122 | JAPAN | FUKUOKA | FKK |
  | 123 | JAPAN | NAHA | NHA |
  | 124 | JAPAN | OSAKA-KOBE | KBO |
  | 125 | JAPAN | SAPPORO | SPP |
  | 126 | JAPAN | TOKYO | TKY |
  | 127 | JERUSALEM | JERUSALEM | JRS |
  | 128 | JORDAN | AMMAN | AMM |
  | 129 | KAZAKHSTAN | ALMATY | ATA |
  | 130 | KAZAKHSTAN | ASTANA | AST |
  | 131 | KENYA | NAIROBI | NRB |
  | 132 | KOSOVO | PRISTINA | PRI |
  | 133 | KUWAIT | KUWAIT | KWT |
  | 134 | KYRGYZSTAN | BISHKEK | BKK |
  | 135 | LAOS | VIENTIANE | VNT |
  | 136 | LATVIA | RIGA | RGA |
  | 137 | LEBANON | BEIRUT | BRT |
  | 138 | LESOTHO | MASERU | MAS |
  | 139 | LIBERIA | MONROVIA | MRV |
  | 140 | LIBYA | TRIPOLI | TRP |
  | 141 | LITHUANIA | VILNIUS | VIL |
  | 142 | LUXEMBOURG | LUXEMBOURG | LXM |
  | 143 | MADAGASCAR | ANTANANARIVO | ANT |
  | 144 | MALAWI | LILONGWE | LIL |
  | 145 | MALAYSIA | KUALA LUMPUR | KLL |
  | 146 | MALI | BAMAKO | BAM |
  | 147 | MALTA | VALLETTA | VLL |
  | 148 | MAURITANIA | NOUAKCHOTT | NUK |
  | 149 | MAURITIUS | PORT LOUIS | PTL |
  | 150 | MEXICO | CIUDAD JUAREZ | CDJ |
  | 151 | MEXICO | GUADALAJARA | GDL |
  | 152 | MEXICO | HERMOSILLO | HER |
  | 153 | MEXICO | MERIDA | MER |
  | 154 | MEXICO | MEXICO CITY | MEX |
  | 155 | MEXICO | MONTERREY | MTR |
  | 156 | MEXICO | NOGALES | NGL |
  | 157 | MEXICO | NUEVO LAREDO | NVL |
  | 158 | MEXICO | TIJUANA | TJN |
  | 159 | MOLDOVA | CHISINAU | CHS |
  | 160 | MONGOLIA | ULAANBAATAR | ULN |
  | 161 | MONTENEGRO | PODGORICA | POD |
  | 162 | MOROCCO | CASABLANCA | CSB |
  | 163 | MOZAMBIQUE | MAPUTO | MAP |
  | 164 | NAMIBIA | WINDHOEK | WHK |
  | 165 | NEPAL | KATHMANDU | KDU |
  | 166 | NETHERLANDS | AMSTERDAM | AMS |
  | 167 | NEW ZEALAND | AUCKLAND | ACK |
  | 168 | NICARAGUA | MANAGUA | MNG |
  | 169 | NIGER | NIAMEY | NMY |
  | 170 | NIGERIA | ABUJA | ABU |
  | 171 | NIGERIA | LAGOS | LGS |
  | 172 | NORTH MACEDONIA | SKOPJE | SKO |
  | 173 | NORTHERN IRELAND | BELFAST | BLF |
  | 174 | NORWAY | OSLO | OSL |
  | 175 | OMAN | MUSCAT | MST |
  | 176 | PAKISTAN | ISLAMABAD | ISL |
  | 177 | PAKISTAN | KARACHI | KRC |
  | 178 | PAKISTAN | LAHORE | LHR |
  | 179 | PAKISTAN | PESHAWAR | PSH |
  | 180 | PANAMA | PANAMA CITY | PNM |
  | 181 | PAPUA NEW GUINEA | PORT MORESBY | PTM |
  | 182 | PARAGUAY | ASUNCION | ASN |
  | 183 | PERU | LIMA | LMA |
  | 184 | PHILIPPINES | MANILA ACS Appointment | MNL |
  | 185 | PHILIPPINES | MN2 U.S. CEBU Consular Agency | MN2 |
  | 186 | POLAND | KRAKOW | KRK |
  | 187 | POLAND | POZNAN | POZ |
  | 188 | POLAND | WARSAW | WRW |
  | 189 | PORTUGAL | PONTA DELGADA | PTD |
  | 190 | PORTUGAL | LISBON | LSB |
  | 191 | QATAR | DOHA | DOH |
  | 192 | REPUBLIC OF KOREA (SOUTH KOREA) | SEOUL ACS Appointment | SEO |
  | 193 | REPUBLIC OF KOREA (SOUTH KOREA) | SEOUL ACS II Appointment | SE2 |
  | 194 | REPUBLIC OF PALAU | KOROR | KOR |
  | 195 | REPUBLIC OF THE MARSHALL ISLANDS | MAJURO | MAJ |
  | 196 | ROMANIA | BUCHAREST | BCH |
  | 197 | RUSSIA | MOSCOW | MOS |
  | 198 | RUSSIA | ST PETERSBURG | SPT |
  | 199 | RUSSIA | VLADIVOSTOK | VLA |
  | 200 | RUSSIA | YEKATERINBURG | YEK |
  | 201 | RWANDA | KIGALI | KGL |
  | 202 | SAMOA | APIA | APA |
  | 203 | SAUDI ARABIA | DHAHRAN | DHR |
  | 204 | SAUDI ARABIA | JEDDAH | JDD |
  | 205 | SAUDI ARABIA | Riyadh | RID |
  | 206 | SENEGAL | DAKAR | DKR |
  | 207 | SERBIA | BELGRADE | BLG |
  | 208 | SIERRA LEONE | FREETOWN | FTN |
  | 209 | SINGAPORE | SINGAPORE | SGP |
  | 210 | SLOVAKIA | BRATISLAVA | BTS |
  | 211 | SLOVENIA | LJUBLJANA | LJU |
  | 212 | SOUTH AFRICA | CAPE TOWN | CPT |
  | 213 | SOUTH AFRICA | DURBAN | DRB |
  | 214 | SOUTH AFRICA | JOHANNESBURG | JHN |
  | 215 | SOUTH SUDAN | JUBA | JBA |
  | 216 | SPAIN | BARCELONA | BRC |
  | 217 | SPAIN | FUENGIROLA (MALAGA) | FUE |
  | 218 | SPAIN | LAS PALMAS | LSP |
  | 219 | SPAIN | MADRID | MDD |
  | 220 | SPAIN | MALLORCA | PDM |
  | 221 | SPAIN | SEVILLE | SVL |
  | 222 | SPAIN | VALENCIA | VLC |
  | 223 | SRI LANKA | COLOMBO | CLM |
  | 224 | SUDAN | KHARTOUM | KHT |
  | 225 | SURINAME | PARAMARIBO | PRM |
  | 226 | SWEDEN | STOCKHOLM | STK |
  | 227 | SWITZERLAND | BERN | BEN |
  | 228 | SWITZERLAND | GENEVA | GVA |
  | 229 | SWITZERLAND | ZURICH | ZRH |
  | 230 | SYRIA | DAMASCUS | DMS |
  | 231 | TAIWAN | KAOHSIUNG | KAO |
  | 232 | TAIWAN | TAIPEI | TAI |
  | 233 | TAJIKISTAN | DUSHANBE | DHB |
  | 234 | TANZANIA | DAR ES SALAAM | DRS |
  | 235 | THAILAND | BANGKOK | BNK |
  | 236 | THAILAND | CHIANG MAI | CHN |
  | 237 | THE GAMBIA | BANJUL | BAN |
  | 238 | TOGO | Lome - U.S. Citizen Services | LOM |
  | 239 | TRINIDAD AND TOBAGO | PORT OF SPAIN | PTS |
  | 240 | TUNISIA | TUNIS | TNS |
  | 241 | TURKEY | ANKARA | ANK |
  | 242 | TURKEY | ISTANBUL | IST |
  | 243 | TURKEY | IZMIR | IZM |
  | 244 | TURKMENISTAN | ASHGABAT | AKD |
  | 245 | UGANDA | KAMPALA | KMP |
  | 246 | UKRAINE | KYIV | KEV |
  | 247 | UNITED ARAB EMIRATES | ABU DHABI | ABD |
  | 248 | UNITED ARAB EMIRATES | DUBAI | DUB |
  | 249 | URUGUAY | MONTEVIDEO | MTV |
  | 250 | UZBEKISTAN | TASHKENT | THT |
  | 251 | VENEZUELA | CARACAS | CRS |
  | 252 | VIETNAM | HANOI | HAN |
  | 253 | VIETNAM | HO CHI MINH CITY | HCM |
  | 254 | YEMEN | SANAA | SAA |
  | 255 | ZAMBIA | LUSAKA | LUS |
  | 256 | ZIMBABWE | HARARE | HRE |

  </details>

- `months`: +非负整数, 表示相对月份, 例如 `["+0", "+1", "+2"]`, 以初始日历页面时上的月份作为基准推算
- `service_index` / `service_indexs`: 服务选择页中的第几个服务, 从 `1` 开始. `service_index` 仅用于单选情况, 输入为单个数字; `service_indexs` 用于可多选情况, 例如 `[1, 3]` 表示选择第 1 个和第 3 个服务. 不得同时使用两个参数. 参数并非随意指定, 必须根据具体城市的服务选择页确定
- `show_browser`: 是否显示浏览器
- `timeout_seconds`: 页面超时时间, 单位秒
- `check_once_max_seconds`: 单次查询最大运行秒数, 超时会强制中止并等待下一次执行
- `interval_minutes`: 轮询间隔, 单位分钟, `0` 表示只执行一次

## 自动预约配置

### 开关

`booking.enabled`

- `true`: 开启自动预约
- `false`: 只查询, 不提交

### 日期筛选

`booking.date_selection` 包含 3 层规则:

1. `targets`

- 支持输入多个日期字符串, 例如 `"2026-05-05"`
- `targets` 为空时, 不按目标日期筛选, 直接在全部可用日期里继续执行后续规则

2. `filter_mode`

- `none`: 不筛选
- `weight`: 使用 `weights` 加权, 只保留权重最大的日期, 长度必须和 `targets` 长度一致, 每个权重必须是非负整数
- `max_available`: 只保留可用名额最多的日期

3. `final_pick`

- `earliest`: 选最早日期
- `latest`: 选最晚日期

### 时间筛选

`booking.time_selection` 包含 2 层规则:

1. `filter_mode`

- `none`: 不筛选
- `max_available`: 只保留可用名额最多的时间

2. `final_pick`

- `earliest`: 选最早时间
- `latest`: 选最晚时间

### 申请人信息

`booking.applicant` 必填字段:

- `last_name`, 姓
- `first_name`, 名
- `date_of_birth`, 格式必须是 `YYYY-MM-DD`
- `telephone`, 电话
- `email`, 邮箱
- `citizenship`, 国籍, 参考[缓存文件](cache/citizenship.md)或下面列表
  <details><summary><code>Country of Citizenship</code></summary>

  | Index | Country of Citizenship |
  | -------- | -------- |
  | 1 | AFGHANISTAN |
  | 2 | ALBANIA |
  | 3 | ALGERIA |
  | 4 | ANDORRA |
  | 5 | ANGOLA |
  | 6 | ANGUILLA |
  | 7 | ANTIGUA AND BARBUDA |
  | 8 | ARGENTINA |
  | 9 | ARMENIA |
  | 10 | ARUBA |
  | 11 | AUSTRALIA |
  | 12 | AUSTRIA |
  | 13 | AZERBAIJAN |
  | 14 | BAHAMAS |
  | 15 | BAHRAIN |
  | 16 | BANGLADESH |
  | 17 | BARBADOS |
  | 18 | BELARUS |
  | 19 | BELGIUM |
  | 20 | BELIZE |
  | 21 | BENIN |
  | 22 | BERMUDA |
  | 23 | BHUTAN |
  | 24 | BOLIVIA |
  | 25 | BOSNIA-HERZEGOVINA |
  | 26 | BOTSWANA |
  | 27 | BRAZIL |
  | 28 | BRITISH INDIAN OCEAN TERRITORY |
  | 29 | BRITISH VIRGIN ISLANDS |
  | 30 | BRUNEI |
  | 31 | BULGARIA |
  | 32 | BURKINA FASO |
  | 33 | BURMA |
  | 34 | BURUNDI |
  | 35 | CAMBODIA |
  | 36 | CAMEROON |
  | 37 | CANADA |
  | 38 | CABO VERDE |
  | 39 | CAYMAN ISLANDS |
  | 40 | CENTRAL AFRICAN REPUBLIC |
  | 41 | CHAD |
  | 42 | CHILE |
  | 43 | CHINA - MAINLAND |
  | 44 | COLOMBIA |
  | 45 | COMOROS |
  | 46 | CONGO - BRAZZAVILLE |
  | 47 | CONGO - KINSHASA |
  | 48 | COSTA RICA |
  | 49 | COTE D IVOIRE |
  | 50 | CROATIA |
  | 51 | CUBA |
  | 52 | CYPRUS |
  | 53 | CZECH REPUBLIC |
  | 54 | DENMARK |
  | 55 | DJIBOUTI |
  | 56 | DOMINICA |
  | 57 | DOMINICAN REPUBLIC |
  | 58 | EAST TIMOR |
  | 59 | ECUADOR |
  | 60 | EGYPT |
  | 61 | EL SALVADOR |
  | 62 | EQUATORIAL GUINEA |
  | 63 | ERITREA |
  | 64 | ESTONIA |
  | 65 | ETHIOPIA |
  | 66 | FEDERATED STATES OF MICRONESIA |
  | 67 | FIJI |
  | 68 | FINLAND |
  | 69 | FRANCE |
  | 70 | GABON |
  | 71 | GEORGIA |
  | 72 | GERMANY |
  | 73 | GHANA |
  | 74 | GIBRALTAR |
  | 75 | GREAT BRITAIN AND NORTHERN IRELAND |
  | 76 | GREECE |
  | 77 | GRENADA |
  | 78 | GUATEMALA |
  | 79 | GUINEA |
  | 80 | GUINEA - BISSAU |
  | 81 | GUYANA |
  | 82 | HAITI |
  | 83 | HONDURAS |
  | 84 | HONG KONG |
  | 85 | HONG KONG S. A. R. |
  | 86 | HUNGARY |
  | 87 | ICELAND |
  | 88 | INDIA |
  | 89 | INDONESIA |
  | 90 | IRAN |
  | 91 | IRAQ |
  | 92 | IRELAND |
  | 93 | ISRAEL |
  | 94 | ITALY |
  | 95 | JAMAICA |
  | 96 | JAPAN |
  | 97 | JORDAN |
  | 98 | KAZAKHSTAN |
  | 99 | KENYA |
  | 100 | KIRIBATI |
  | 101 | KOSOVO |
  | 102 | KUWAIT |
  | 103 | KYRGYZSTAN |
  | 104 | LAOS |
  | 105 | LATVIA |
  | 106 | LEBANON |
  | 107 | LESOTHO |
  | 108 | LIBERIA |
  | 109 | LIBYA |
  | 110 | LIECHTENSTEIN |
  | 111 | LITHUANIA |
  | 112 | LUXEMBOURG |
  | 113 | MACAU |
  | 114 | MADAGASCAR |
  | 115 | MALAWI |
  | 116 | MALAYSIA |
  | 117 | MALDIVES |
  | 118 | MALI |
  | 119 | MALTA |
  | 120 | MAURITANIA |
  | 121 | MAURITIUS |
  | 122 | MEXICO |
  | 123 | MOLDOVA |
  | 124 | MONACO |
  | 125 | MONGOLIA |
  | 126 | MONTSERRAT |
  | 127 | MOROCCO |
  | 128 | MOZAMBIQUE |
  | 129 | NAMIBIA |
  | 130 | NAURU |
  | 131 | NEPAL |
  | 132 | NETHERLANDS |
  | 133 | NETHERLANDS ANTILLES |
  | 134 | NEW CALEDONIA |
  | 135 | NEW ZEALAND |
  | 136 | NICARAGUA |
  | 137 | NIGER |
  | 138 | NIGERIA |
  | 139 | NORWAY |
  | 140 | OMAN |
  | 141 | PAKISTAN |
  | 142 | PALESTINIAN AUTHORITY |
  | 143 | PANAMA |
  | 144 | PAPUA NEW GUINEA |
  | 145 | PARAGUAY |
  | 146 | PEOPLES REPUBLIC OF KOREA - NORTH KOREA |
  | 147 | PERU |
  | 148 | PHILIPPINES |
  | 149 | PITCAIRN ISLANDS |
  | 150 | POLAND |
  | 151 | PORTUGAL |
  | 152 | QATAR |
  | 153 | REPUBLIC OF KOREA - SOUTH KOREA |
  | 154 | REPUBLIC OF MACEDONIA |
  | 155 | REPUBLIC OF PALAU |
  | 156 | REPUBLIC OF THE MARSHALL ISLANDS |
  | 157 | ROMANIA |
  | 158 | RUSSIA |
  | 159 | RWANDA |
  | 160 | SAMOA |
  | 161 | SAN MARINO |
  | 162 | SAO TOME AND PRINCIPE |
  | 163 | SAUDI ARABIA |
  | 164 | SENEGAL |
  | 165 | SERBIA AND MONTENEGRO |
  | 166 | SEYCHELLES |
  | 167 | SIERRA LEONE |
  | 168 | SINGAPORE |
  | 169 | SLOVAKIA |
  | 170 | SLOVENIA |
  | 171 | SOLOMON ISLANDS |
  | 172 | SOMALIA |
  | 173 | SOUTH AFRICA |
  | 174 | SPAIN |
  | 175 | SRI LANKA |
  | 176 | ST. HELENA |
  | 177 | ST. KITTS AND NEVIS |
  | 178 | ST. LUCIA |
  | 179 | ST. VINCENT AND THE GRENADINES |
  | 180 | SUDAN |
  | 181 | SURINAME |
  | 182 | SWAZILAND |
  | 183 | SWEDEN |
  | 184 | SWITZERLAND |
  | 185 | SYRIA |
  | 186 | TAIWAN |
  | 187 | TAJIKISTAN |
  | 188 | TANZANIA |
  | 189 | THAILAND |
  | 190 | THE GAMBIA |
  | 191 | TOGO |
  | 192 | TONGA |
  | 193 | TRINIDAD AND TOBAGO |
  | 194 | TUNISIA |
  | 195 | TURKEY |
  | 196 | TURKMENISTAN |
  | 197 | TURKS AND CAICOS ISLANDS |
  | 198 | TUVALU |
  | 199 | UGANDA |
  | 200 | UKRAINE |
  | 201 | UNITED ARAB EMIRATES |
  | 202 | UNITED NATIONS LAISSEZ-PASSER |
  | 203 | UNITED STATES OF AMERICA |
  | 204 | URUGUAY |
  | 205 | UZBEKISTAN |
  | 206 | VANUATU |
  | 207 | VATICAN CITY |
  | 208 | VENEZUELA |
  | 209 | VIETNAM |
  | 210 | WALLIS AND FUTUNA ISLANDS |
  | 211 | WESTERN SAHARA |
  | 212 | YEMEN |
  | 213 | ZAMBIA |
  | 214 | ZIMBABWE |

  </details>

- `birth_country`, 出生国家/地区, 参考[缓存文件](cache/birthcountry.md)或下面列表
  <details><summary><code>Country of Birth</code></summary>

  | Index | Country of Birth |
  | -------- | -------- |
  | 1 | AFGHANISTAN |
  | 2 | ALBANIA |
  | 3 | ALGERIA |
  | 4 | AMERICAN SAMOA |
  | 5 | ANDORRA |
  | 6 | ANGOLA |
  | 7 | ANGUILLA |
  | 8 | ANTIGUA AND BARBUDA |
  | 9 | ARGENTINA |
  | 10 | ARMENIA |
  | 11 | ARUBA |
  | 12 | AT SEA |
  | 13 | AUSTRALIA |
  | 14 | AUSTRIA |
  | 15 | AZERBAIJAN |
  | 16 | BAHAMAS |
  | 17 | BAHRAIN |
  | 18 | BAKER ISLAND |
  | 19 | BANGLADESH |
  | 20 | BARBADOS |
  | 21 | BELARUS |
  | 22 | BELGIUM |
  | 23 | BELIZE |
  | 24 | BENIN |
  | 25 | BERMUDA |
  | 26 | BESSARABIA |
  | 27 | BHUTAN |
  | 28 | BOLIVIA |
  | 29 | BOSNIA-HERZEGOVINA |
  | 30 | BOTSWANA |
  | 31 | BRAZIL |
  | 32 | BRITISH INDIAN OCEAN TERRITORY |
  | 33 | BRITISH VIRGIN ISLANDS |
  | 34 | BRUNEI |
  | 35 | BULGARIA |
  | 36 | BURKINA FASO |
  | 37 | BURMA |
  | 38 | BURUNDI |
  | 39 | CAMBODIA |
  | 40 | CAMEROON |
  | 41 | CANADA |
  | 42 | CABO VERDE |
  | 43 | CAYMAN ISLANDS |
  | 44 | CENTRAL AFRICAN REPUBLIC |
  | 45 | CHAD |
  | 46 | CHILE |
  | 47 | CHINA - MAINLAND |
  | 48 | CHRISTMAS ISLAND |
  | 49 | COCOS KEELING ISLANDS |
  | 50 | COLOMBIA |
  | 51 | COMOROS |
  | 52 | CONGO - BRAZZAVILLE |
  | 53 | CONGO - KINSHASA |
  | 54 | COOK ISLANDS |
  | 55 | COSTA RICA |
  | 56 | COTE D IVOIRE |
  | 57 | CROATIA |
  | 58 | CUBA |
  | 59 | CYPRUS |
  | 60 | CZECH REPUBLIC |
  | 61 | DANZIG |
  | 62 | DENMARK |
  | 63 | DJIBOUTI |
  | 64 | DOMINICA |
  | 65 | DOMINICAN REPUBLIC |
  | 66 | EAST PRUSSIA |
  | 67 | EAST TIMOR |
  | 68 | ECUADOR |
  | 69 | EGYPT |
  | 70 | EL SALVADOR |
  | 71 | EQUATORIAL GUINEA |
  | 72 | ERITREA |
  | 73 | ESTONIA |
  | 74 | ETHIOPIA |
  | 75 | FALKLAND ISLANDS |
  | 76 | FAROE ISLANDS |
  | 77 | FEDERATED STATES OF MICRONESIA |
  | 78 | FIJI |
  | 79 | FINLAND |
  | 80 | FRANCE |
  | 81 | FRENCH GUIANA |
  | 82 | FRENCH POLYNESIA |
  | 83 | FRENCH SOUTHERN - ANTARCTIC TERRITORIES |
  | 84 | GABON |
  | 85 | GAZA STRIP |
  | 86 | GDANSK |
  | 87 | GEORGIA |
  | 88 | GERMANY |
  | 89 | GHANA |
  | 90 | GIBRALTAR |
  | 91 | GREAT BRITAIN AND NORTHERN IRELAND |
  | 92 | GREECE |
  | 93 | GREENLAND |
  | 94 | GRENADA |
  | 95 | GUADELOUPE |
  | 96 | GUAM |
  | 97 | GUATEMALA |
  | 98 | GUINEA |
  | 99 | GUINEA - BISSAU |
  | 100 | GUYANA |
  | 101 | HAITI |
  | 102 | HEARD AND MCDONALD ISLANDS |
  | 103 | HONDURAS |
  | 104 | HONG KONG |
  | 105 | HONG KONG S. A. R. |
  | 106 | HOWLAND ISLAND |
  | 107 | HUNGARY |
  | 108 | ICELAND |
  | 109 | IN THE AIR |
  | 110 | INDIA |
  | 111 | INDONESIA |
  | 112 | IRAN |
  | 113 | IRAQ |
  | 114 | IRELAND |
  | 115 | ISRAEL |
  | 116 | ITALY |
  | 117 | JAMAICA |
  | 118 | JAPAN |
  | 119 | JOHNSTON ATOLL |
  | 120 | JORDAN |
  | 121 | KAZAKHSTAN |
  | 122 | KENYA |
  | 123 | KIRIBATI |
  | 124 | KOSOVO |
  | 125 | KUWAIT |
  | 126 | KYRGYZSTAN |
  | 127 | LAOS |
  | 128 | LATVIA |
  | 129 | LEBANON |
  | 130 | LESOTHO |
  | 131 | LIBERIA |
  | 132 | LIBYA |
  | 133 | LIECHTENSTEIN |
  | 134 | LITHUANIA |
  | 135 | LUXEMBOURG |
  | 136 | MACAU |
  | 137 | MADAGASCAR |
  | 138 | MALAWI |
  | 139 | MALAYSIA |
  | 140 | MALDEN ISLAND |
  | 141 | MALDIVES |
  | 142 | MALI |
  | 143 | MALTA |
  | 144 | MARTINIQUE |
  | 145 | MAURITANIA |
  | 146 | MAURITIUS |
  | 147 | MAYOTTE |
  | 148 | MEXICO - AGUASCALIENTES |
  | 149 | MEXICO - BAJA CALIFORNIA NORTE |
  | 150 | MEXICO - BAJA CALIFORNIA SUR |
  | 151 | MEXICO - CAMPECHE |
  | 152 | MEXICO - CHIAPAS |
  | 153 | MEXICO - CHIHUAHUA |
  | 154 | MEXICO - COAHUILA |
  | 155 | MEXICO - COLIMA |
  | 156 | MEXICO - DISTRITO FEDERAL |
  | 157 | MEXICO - DURANGO |
  | 158 | MEXICO - GUANAJUATO |
  | 159 | MEXICO - GUERRERO |
  | 160 | MEXICO - HIDALGO |
  | 161 | MEXICO - JALISCO |
  | 162 | MEXICO - MICHOACAN |
  | 163 | MEXICO - MORELOS |
  | 164 | MEXICO - NAYARIT |
  | 165 | MEXICO - NUEVO LEON |
  | 166 | MEXICO - OAXACA |
  | 167 | MEXICO - PUEBLA |
  | 168 | MEXICO - QUERETARO |
  | 169 | MEXICO - QUINTANA ROO |
  | 170 | MEXICO - SAN LUIS POTOSI |
  | 171 | MEXICO - SINALOA |
  | 172 | MEXICO - SONORA |
  | 173 | MEXICO - STATE OF MEXICO |
  | 174 | MEXICO - TABASCO |
  | 175 | MEXICO - TAMAULIPAS |
  | 176 | MEXICO - TLAXCALA |
  | 177 | MEXICO - VERACRUZ |
  | 178 | MEXICO - YUCATAN |
  | 179 | MEXICO - ZACATECAS |
  | 180 | MIDWAY ISLANDS |
  | 181 | MOLDOVA |
  | 182 | MONACO |
  | 183 | MONGOLIA |
  | 184 | MONTSERRAT |
  | 185 | MOROCCO |
  | 186 | MOZAMBIQUE |
  | 187 | NAMIBIA |
  | 188 | NAURU |
  | 189 | NEPAL |
  | 190 | NETHERLANDS |
  | 191 | NETHERLANDS ANTILLES |
  | 192 | NEW CALEDONIA |
  | 193 | NEW ZEALAND |
  | 194 | NICARAGUA |
  | 195 | NIGER |
  | 196 | NIGERIA |
  | 197 | NIUE |
  | 198 | NO MARIANA ISLANDS - USA |
  | 199 | NORTHERN IRELAND |
  | 200 | NORWAY |
  | 201 | OMAN |
  | 202 | PAKISTAN |
  | 203 | PALMYRA ATOLL |
  | 204 | PANAMA |
  | 205 | PAPUA NEW GUINEA |
  | 206 | PARAGUAY |
  | 207 | PEOPLES REPUBLIC OF KOREA - NORTH KOREA |
  | 208 | PERU |
  | 209 | PHILIPPINES |
  | 210 | PITCAIRN ISLANDS |
  | 211 | POLAND |
  | 212 | PORTUGAL |
  | 213 | PUERTO RICO |
  | 214 | QATAR |
  | 215 | REPUBLIC OF KOREA - SOUTH KOREA |
  | 216 | REPUBLIC OF MACEDONIA |
  | 217 | REPUBLIC OF PALAU |
  | 218 | REPUBLIC OF THE MARSHALL ISLANDS |
  | 219 | REUNION |
  | 220 | ROMANIA |
  | 221 | RUSSIA |
  | 222 | RWANDA |
  | 223 | SAMOA |
  | 224 | SAN MARINO |
  | 225 | SAO TOME AND PRINCIPE |
  | 226 | SAUDI ARABIA |
  | 227 | SENEGAL |
  | 228 | SERBIA AND MONTENEGRO |
  | 229 | SEYCHELLES |
  | 230 | SIERRA LEONE |
  | 231 | SINGAPORE |
  | 232 | SLOVAKIA |
  | 233 | SLOVENIA |
  | 234 | SOLOMON ISLANDS |
  | 235 | SOMALIA |
  | 236 | SOUTH AFRICA |
  | 237 | SPAIN |
  | 238 | SRI LANKA |
  | 239 | ST MARTIN |
  | 240 | ST. HELENA |
  | 241 | ST. KITTS AND NEVIS |
  | 242 | ST. LUCIA |
  | 243 | ST. PIERRE - MIQUELON |
  | 244 | ST. VINCENT AND THE GRENADINES |
  | 245 | SUDAN |
  | 246 | SURINAME |
  | 247 | SWAZILAND |
  | 248 | SWEDEN |
  | 249 | SWITZERLAND |
  | 250 | SYRIA |
  | 251 | TAIWAN |
  | 252 | TAJIKISTAN |
  | 253 | TANZANIA |
  | 254 | THAILAND |
  | 255 | THE GAMBIA |
  | 256 | TOGO |
  | 257 | TOKELAU |
  | 258 | TONGA |
  | 259 | TRINIDAD AND TOBAGO |
  | 260 | TUNISIA |
  | 261 | TURKEY |
  | 262 | TURKMENISTAN |
  | 263 | TURKS AND CAICOS ISLANDS |
  | 264 | TUVALU |
  | 265 | UGANDA |
  | 266 | UKRAINE |
  | 267 | UNITED ARAB EMIRATES |
  | 268 | UNITED STATES OF AMERICA |
  | 269 | URUGUAY |
  | 270 | UZBEKISTAN |
  | 271 | VANUATU |
  | 272 | VATICAN CITY |
  | 273 | VENEZUELA |
  | 274 | VIETNAM |
  | 275 | VIRGIN ISLANDS - U.S. |
  | 276 | WAKE ISLAND |
  | 277 | WALLIS AND FUTUNA ISLANDS |
  | 278 | WEST BANK |
  | 279 | WESTERN SAHARA |
  | 280 | YEMEN |
  | 281 | ZAMBIA |
  | 282 | ZIMBABWE |

  </details>

- `sex`, 性别, 只能是 `M` 或 `F`
- `passport_number`, 护照号码
- `non_applicant_names` 所有计划陪同申请人前往使领馆的非申请人姓名列表, 例如 `["John Doe", "Jane Doe"]`, 可以为空

如果这些字段不完整或错误, 脚本会打印错误并等待下一次轮询, 不会继续提交

### Bubble 预约

`booking.bubble` 用于已有预约或未预约时自动改约到更优日期

- `enabled`
  - `true`: 开启 Bubble 模式
  - `false`: 关闭 Bubble 模式
- `password`
  - 当前预约的密码
  - 同城市同信息系统只允许同时预约一次, 如有预约请填写, 否则留空, 脚本会用它查询并取消当前预约后再新预约

Bubble 实际生效需要同时满足:

- `booking.enabled = true`
- `booking.bubble.enabled = true`
- `booking.date_selection.filter_mode` 只能是 `none` 或 `weight`

执行逻辑:

1. 如果尚未确认当前预约且已配置 `booking.bubble.password`, 脚本会先进入取消预约查询页, 使用 `last_name`、`first_name`、`telephone`、`password` 查询当前预约日期
2. 按 `booking.date_selection` 规则判断是否存在更优日期
3. 如果没有更优日期, 本轮不提交预约, 等待下一次轮询
4. 如果有更优日期, 且拿到了当前预约密码, 会先取消当前预约, 再发起新预约
5. 新预约成功后, 脚本会记录新的预约日期与密码, 供后续轮询继续比较
6. Bubble 模式下, 程序不会主动停止, `interval_minutes` 非 0 时会一直轮询, 请谨慎使用

## 自动预约执行逻辑

1. 获取会话 `cookie` 和 `CSRFToken`
2. 查询指定月份的日历
3. 打印地点, 服务, 月份, 可预约日期
4. 如果 `booking.enabled = true`, 按规则选出预约日期
5. 打开该日期对应的预约页面
6. 如果页面不是预约详情页, 立即重新获取日历并重试
7. 按规则选出预约时间
8. 填写申请人表单
9. 点击 `Continue`
10. 如果进入确认页, 打印预约信息, 保存截图（PNG 和 PDF）、保存 HTML、保存 JSON、保存文本, 然后结束脚本
11. 如果没有进入确认页, 立即重新获取日历并重试

成功后会保存在 `booking_artifacts` 目录:

- 确认页截图
- 确认页截图 PDF
- 确认页 HTML
- 结构化 JSON 信息
- 页面纯文本信息
