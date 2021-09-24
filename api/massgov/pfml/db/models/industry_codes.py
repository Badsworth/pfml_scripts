from sqlalchemy import Column, Integer, Text

from ..lookup import LookupTable
from .base import Base


class LkIndustryCode(Base):
    __tablename__ = "lk_industry_code"
    industry_code_id = Column(Integer, primary_key=True, autoincrement=True)
    industry_code_description = Column(Text, nullable=False)
    industry_code_naics_code = Column(Integer, nullable=False)

    def __init__(self, industry_code_id, industry_code_description, industry_code_naics_code):
        self.industry_code_id = industry_code_id
        self.industry_code_description = industry_code_description
        self.industry_code_naics_code = industry_code_naics_code


class IndustryCode(LookupTable):
    model = LkIndustryCode
    column_names = (
        "industry_code_id",
        "industry_code_description",
        "industry_code_naics_code",
    )

    OILSEED_AND_GRAIN_FARMING = LkIndustryCode(1, "Oilseed and Grain Farming", 1111)
    VEGETABLE_AND_MELON_FARMING = LkIndustryCode(2, "Vegetable and Melon Farming", 1112)
    FRUIT_AND_TREE_NUT_FARMING = LkIndustryCode(3, "Fruit and Tree Nut Farming", 1113)
    GREENHOUSE_NURSERY_AND_FLORICULTURE_PRODUCTION = LkIndustryCode(
        4, "Greenhouse, Nursery, and Floriculture Production", 1114
    )
    OTHER_CROP_FARMING = LkIndustryCode(5, "Other Crop Farming", 1119)
    CATTLE_RANCHING_AND_FARMING = LkIndustryCode(6, "Cattle Ranching and Farming", 1121)
    HOG_AND_PIG_FARMING = LkIndustryCode(7, "Hog and Pig Farming", 1122)
    POULTRY_AND_EGG_PRODUCTION = LkIndustryCode(8, "Poultry and Egg Production", 1123)
    SHEEP_AND_GOAT_FARMING = LkIndustryCode(9, "Sheep and Goat Farming", 1124)
    AQUACULTURE = LkIndustryCode(10, "Aquaculture", 1125)
    OTHER_ANIMAL_PRODUCTION = LkIndustryCode(11, "Other Animal Production", 1129)
    TIMBER_TRACT_OPERATION = LkIndustryCode(12, "Timber Tract Operations", 1131)
    FOREST_NURSERIES_AND_GATHERING_OF_FOREST_PRODUCTS = LkIndustryCode(
        13, "Forest Nurseries and Gathering of Forest Products", 1132
    )
    LOGGING = LkIndustryCode(14, "Logging", 1133)
    FISHING = LkIndustryCode(15, "Fishing", 1141)
    HUNTING_AND_TRAPPING = LkIndustryCode(16, "Hunting and Trapping", 1142)
    SUPPORT_ACTIVITIES_FOR_CROP_PRODUCTION = LkIndustryCode(
        17, "Support Activities for Crop Production", 1151
    )
    SUPPORT_ACTIVITIES_FOR_ANIMAL_PRODUCTION = LkIndustryCode(
        18, "Support Activities for Animal Production", 1152
    )
    SUPPORT_ACTIVITIES_FOR_FORESTRY = LkIndustryCode(19, "Support Activities for Forestry", 1153)

    OIL_AND_GAS_EXTRACTION = LkIndustryCode(20, "Oil and Gas Extraction", 2111)
    COAL_MINING = LkIndustryCode(21, "Coal Mining", 2121)
    METAL_ORE_MINING = LkIndustryCode(22, "Metal Ore Mining", 2122)
    NONMETALLIC_MINERAL_MINING_AND_QUARRYING = LkIndustryCode(
        23, "Nonmetallic Mineral Mining and Quarrying", 2123
    )
    SUPPORT_ACTIVITIES_FOR_MINING = LkIndustryCode(24, "Support Activities for Mining", 2131)

    ELECTRIC_POWER_GENERATION_TRANSMISSION_AND_DISTRIBUTION = LkIndustryCode(
        25, "Electric Power Generation, Transmission and Distribution", 2211
    )
    NATURAL_GAS_DISTRIBUTION = LkIndustryCode(26, "Natural Gas Distribution", 2212)
    WATER_SEWAGE_AND_OTHER_SYSTEMS = LkIndustryCode(27, "Water, Sewage and Other Systems", 2213)

    RESIDENTIAL_BUILDING_CONSTRUCTION = LkIndustryCode(
        28, "Residential Building Construction", 2361
    )
    NONRESIDENTIAL_BUILDING_CONSTRUCTION = LkIndustryCode(
        29, "Nonresidential Building Construction", 2362
    )
    UTILITY_SYSTEM_CONSTRUCTION = LkIndustryCode(30, "Utility System Construction", 2371)
    LAND_SUBDIVISION = LkIndustryCode(31, "Land Subdivision", 2372)
    HIGH_STREET_AND_BRIDGE_CONSTRUCTION = LkIndustryCode(
        32, "Highway, Street, and Bridge Construction", 2373
    )
    OTHER_HEAVY_AND_CIVIL_ENGINEERING_CONSTRUCTION = LkIndustryCode(
        33, "Other Heavy and Civil Engineering Construction", 2379
    )
    FOUNDATION_STRUCTURE_AND_BUILDING_EXTERIOR_CONTRACTORS = LkIndustryCode(
        34, "Foundation, Structure, and Building Exterior Contractors", 2381
    )
    BUILDING_EQUIPMENT_CONTRACTORS = LkIndustryCode(35, "Building Equipment Contractors", 2382)
    BUILDING_FINISHING_CONTRACTORS = LkIndustryCode(36, "Building Finishing Contractors", 2383)
    OTHER_SPECIALTY_TRADE_CONTRACTORS = LkIndustryCode(
        37, "Other Specialty Trade Contractors", 2389
    )

    ANIMAL_FOOD_MANUFACTURING = LkIndustryCode(38, "Animal Food Manufacturing", 3111)
    GRAIN_AND_OILSEED_MILLING = LkIndustryCode(39, "Grain and Oilseed Milling", 3112)
    SUGAR_AND_CONFECTIONERY_PRODUCT_MANUFACTURING = LkIndustryCode(
        40, "Sugar and Confectionery Product Manufacturing", 3113
    )
    FRUIT_AND_VEGETABLE_PRESERVING_AND_SPECIALTY_FOOD_MANUFACTURING = LkIndustryCode(
        41, "Fruit and Vegetable Preserving and Specialty Food Manufacturing", 3114
    )
    DAIRY_PRODUCT_MANUFACTURING = LkIndustryCode(42, "Dairy Product Manufacturing", 3115)
    ANIMAL_SLAUGHTERING_AND_PROCESSING = LkIndustryCode(
        43, "Animal Slaughtering and Processing", 3116
    )
    SEAFOOD_PRODUCT_PREPARATION_AND_PACKAGING = LkIndustryCode(
        44, "Seafood Product Preparation and Packaging", 3117
    )
    BAKERIES_AND_TORTILLA_MANUFACTURING = LkIndustryCode(
        45, "Bakeries and Tortilla Manufacturing", 3118
    )
    OTHER_FOOD_MANUFACTURING = LkIndustryCode(46, "Other Food Manufacturing", 3119)
    BEVERAGE_MANUFACTURING = LkIndustryCode(47, "Beverage Manufacturing", 3121)
    TOBACCO_MANUFACTURING = LkIndustryCode(48, "Tobacco Manufacturing", 3122)
    FIBER_YARN_AND_THREAD_MILLS = LkIndustryCode(49, "Fiber, Yarn, and Thread Mills", 3131)
    FABRIC_MILLS = LkIndustryCode(50, "Fabric Mills", 3132)
    TEXTILE_AND_FABRIC_FINISHING_AND_FABRIC_COATING_MILLS = LkIndustryCode(
        51, "Textile and Fabric Finishing and Fabric Coating Mills", 3133
    )
    TEXTILE_FURNISHINGS_MILLS = LkIndustryCode(52, "Textile Furnishings Mills", 3141)
    OTHER_TEXTILE_PRODUCT_MILLS = LkIndustryCode(53, "Other Textile Product Mills", 3149)
    APPAREL_KNITTING_MILLS = LkIndustryCode(54, "Apparel Knitting Mills", 3151)
    CUT_AND_SEW_APPAREL_MANUFACTURING = LkIndustryCode(
        55, "Cut and Sew Apparel Manufacturing", 3152
    )
    APPAREL_ACCESSORIES_AND_OTHER_APPAREL_MANUFACTURING = LkIndustryCode(
        56, "Apparel Accessories and Other Apparel Manufacturing", 3159
    )
    LEATHER_AND_HIDE_TANNING_AND_FINISHING = LkIndustryCode(
        57, "Leather and Hide Tanning and Finishing", 3161
    )
    FOOTWEAR_MANUFACTURING = LkIndustryCode(58, "Footwear Manufacturing", 3162)
    OTHER_LEATHER_AND_ALLIED_PRODUCT_MANUFACTURING = LkIndustryCode(
        59, "Other Leather and Allied Product Manufacturing", 3169
    )
    SAWMILLS_AND_WOOD_PRESERVATION = LkIndustryCode(60, "Sawmills and Wood Preservation", 3211)
    VENEER_PLYWOOD_AND_ENGINEERED_WOOD_PRODUCT_MANUFACTURING = LkIndustryCode(
        61, "Veneer, Plywood, and Engineered Wood Product Manufacturing", 3212
    )
    OTHER_WOOD_PRODUCT_MANUFACTURING = LkIndustryCode(62, "Other Wood Product Manufacturing", 3219)
    PULP_PAPER_AND_PAPERBOARD_MILLS = LkIndustryCode(63, "Pulp, Paper, and Paperboard Mills", 3221)
    CONVERTED_PAPER_PRODUCT_MANUFACTURING = LkIndustryCode(
        64, "Converted Paper Product Manufacturing", 3222
    )
    PRINTING_AND_RELATED_SUPPORT_ACTIVITIES = LkIndustryCode(
        65, "Printing and Related Support Activities", 3231
    )
    PETROLEUM_AND_COAL_PRODUCTS_MANUFACTURING = LkIndustryCode(
        66, "Petroleum and Coal Products Manufacturing", 3241
    )
    BASIC_CHEMICAL_MANUFACTURING = LkIndustryCode(67, "Basic Chemical Manufacturing", 3251)
    RESIN_SYNTHETIC_RUBBER_AND_ARTIFICIAL_AND_SYNTHETIC_FIBERS_AND_FILAMENTS_MANUFACTURING = LkIndustryCode(
        68,
        "Resin, Synthetic Rubber, and Artificial and Synthetic Fibers and Filaments Manufacturing",
        3252,
    )
    PESTICIDE_FERTILIZER_AND_OTHER_AGRICULTURAL_CHEMICAL_MANUFACTURING = LkIndustryCode(
        69, "Pesticide, Fertilizer, and Other Agricultural Chemical Manufacturing", 3253
    )
    PHARMACEUTICAL_AND_MEDICINE_MANUFACTURING = LkIndustryCode(
        70, "Pharmaceutical and Medicine Manufacturing", 3254
    )
    PAINT_COATING_AND_ADHESIVE_MANUFACTURING = LkIndustryCode(
        71, "Paint, Coating, and Adhesive Manufacturing", 3255
    )
    SOAP_CLEANING_COMPOUND_AND_TOILET_PREPARATION_MANUFACTURING = LkIndustryCode(
        72, "Soap, Cleaning Compound, and Toilet Preparation Manufacturing", 3256
    )
    OTHER_CHEMICAL_PRODUCT_AND_PREPARATION_MANUFACTURING = LkIndustryCode(
        73, "Other Chemical Product and Preparation Manufacturing", 3259
    )
    PLASTIC_PRODUCT_MANUFACTURING = LkIndustryCode(74, "Plastics Product Manufacturing", 3261)
    RUBBER_PRODUCT_MANUFACTURING = LkIndustryCode(75, "Rubber Product Manufacturing", 3262)
    CLAY_PRODUCT_AND_REFRACTORY_MANUFACTURING = LkIndustryCode(
        76, "Clay Product and Refractory Manufacturing", 3271
    )
    GLASS_AND_GLASS_PRODUCT_MANUFACTURING = LkIndustryCode(
        77, "Glass and Glass Product Manufacturing", 3272
    )
    CEMENT_AND_CONCRETE_PRODUCT_MANUFACTURING = LkIndustryCode(
        78, "Cement and Concrete Product Manufacturing", 3273
    )
    LIME_AND_GYPSUM_PRODUCT_MANUFACTURING = LkIndustryCode(
        79, "Lime and Gypsum Product Manufacturing", 3274
    )
    OTHER_NONMETALLIC_MINERAL__PRODUCT_MANUFACTURING = LkIndustryCode(
        80, "Other Nonmetallic Mineral Product Manufacturing", 3279
    )
    IRON_AND_STEEL_MILLS_AND_FERROALLOY_MANUFACTURING = LkIndustryCode(
        81, "Iron and Steel Mills and Ferroalloy Manufacturing", 3311
    )
    STEEL_PRODUCT_MANUFACTURING_FROM_PURCHASED_STEEL = LkIndustryCode(
        82, "Steel Product Manufacturing from Purchased Steel", 3312
    )
    ALUMINA_AND_ALUMINUM_PRODUCTION_AND_PROCESSING = LkIndustryCode(
        83, "Alumina and Aluminum Production and Processing", 3313
    )
    NONFERROUS_METAL_EXCEPT_ALUMINUM_PRODUCTION_AND_PROCESSING = LkIndustryCode(
        84, "Nonferrous Metal (except Aluminum) Production and Processing", 3314
    )
    FOUNDRIES = LkIndustryCode(85, "Foundries", 3315)
    FORGING_AND_STAMPING = LkIndustryCode(86, "Forging and Stamping", 3321)
    CUTLERY_AND_HANDTOOL_MANUFACTURING = LkIndustryCode(
        87, "Cutlery and Handtool Manufacturing", 3322
    )
    ARCHITECTURAL_AND_STRUCTURAL_METALS_MANUFACTURING = LkIndustryCode(
        88, "Architectural and Structural Metals Manufacturing", 3323
    )
    BOILER_TANK_AND_SHIPPING_CONTAINER_MANUFACTURING = LkIndustryCode(
        89, "Boiler, Tank, and Shipping Container Manufacturing", 3324
    )
    HARDWARE_MANUFACTURING = LkIndustryCode(90, "Hardware Manufacturing", 3325)
    SPRING_AND_WIRE_PRODUCT_MANUFACTURING = LkIndustryCode(
        91, "Spring and Wire Product Manufacturing", 3326
    )
    MACHINE_SHOPS_TURNED_PRODUCT_AND_SCREW_NUT_AND_BOLT_MANUFACTURING = LkIndustryCode(
        92, "Machine Shops; Turned Product; and Screw, Nut, and Bolt Manufacturing", 3327
    )
    COATING_ENGRAVING_HEAT_TREATING_AND_ALLIED_ACTIVITIES = LkIndustryCode(
        93, "Coating, Engraving, Heat Treating, and Allied Activities", 3328
    )
    OTHER_FABRICATED_METAL_PRODUCT_MANUFACTURING = LkIndustryCode(
        94, "Other Fabricated Metal Product Manufacturing", 3329
    )
    AGRICULTURE_CONSTRUCTION_AND_MINING_MACHINERY_MANUFACTURING = LkIndustryCode(
        95, "Agriculture, Construction, and Mining Machinery Manufacturing", 3331
    )
    INDUSTRIAL_MACHINERY_MANUFACTURING = LkIndustryCode(
        96, "Industrial Machinery Manufacturing", 3332
    )
    COMMERCIAL_AND_SERVICE_INDUSTRY_MACHINERY_MANUFACTURING = LkIndustryCode(
        97, "Commercial and Service Industry Machinery Manufacturing", 3333
    )
    VENTILATION_HEATING_AIR_CONDITIONING_AND_COMMERCIAL_REFRIGERATION_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        98,
        "Ventilation, Heating, Air-Conditioning, and Commercial Refrigeration Equipment Manufacturing",
        3334,
    )
    METALWORKING_MACHINERY_MANUFACTURING = LkIndustryCode(
        99, "Metalworking Machinery Manufacturing", 3335
    )
    ENGINE_TURBINE_AND_POWER_TRANSMISSION_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        100, "Engine, Turbine, and Power Transmission Equipment Manufacturing", 3336
    )
    OTHER_GENERAL_PURPOSE_MACHINERY_MANUFACTURING = LkIndustryCode(
        101, "Other General Purpose Machinery Manufacturing", 3339
    )
    COMPUTER_AND_PERIPHERAL_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        102, "Computer and Peripheral Equipment Manufacturing", 3341
    )
    COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        103, "Communications Equipment Manufacturing", 3342
    )
    AUDIO_AND_VIDEO_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        104, "Audio and Video Equipment Manufacturing", 3343
    )
    SEMICONDUCTOR_AND_OTHER_ELECTRONIC_COMPONENT_MANUFACTURING = LkIndustryCode(
        105, "Semiconductor and Other Electronic Component Manufacturing", 3344
    )
    NAVIGATIONAL_MEASURING_ELECTROMEDICAL_AND_CONTROL_INSTRUMENTS_MANUFACTURING = LkIndustryCode(
        106, "Navigational, Measuring, Electromedical, and Control Instruments Manufacturing", 3345
    )
    MANUFACTURING_AND_REPRODUCING_MAGNETIC_AND_OPTICAL_MEDIA = LkIndustryCode(
        107, "Manufacturing and Reproducing Magnetic and Optical Media", 3346
    )
    ELECTRIC_LIGHTING_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        108, "Electric Lighting Equipment Manufacturing", 3351
    )
    HOUSEHOLD_APPLIANCE_MANUFACTURING = LkIndustryCode(
        109, "Household Appliance Manufacturing", 3352
    )
    ELECTRICAL_APPLIANCE_MANUFACTURING = LkIndustryCode(
        110, "Electrical Equipment Manufacturing", 3353
    )
    OTHER_ELECTRICAL_EQUIPMENT_AND_COMPONENT_MANUFACTURING = LkIndustryCode(
        111, "Other Electrical Equipment and Component Manufacturing", 3359
    )
    MOTOR_VEHICLE_MANUFACTURING = LkIndustryCode(112, "Motor Vehicle Manufacturing", 3361)
    MOTOR_VEHICLE_BODY_AND_TRAILER_MANUFACTURING = LkIndustryCode(
        113, "Motor Vehicle Body and Trailer Manufacturing", 3362
    )
    MOTOR_VEHICLE_PARTS_MANUFACTURING = LkIndustryCode(
        114, "Motor Vehicle Parts Manufacturing", 3363
    )
    AEROSPACE_PRODUCT_AND_PARTS_MANUFACTURING = LkIndustryCode(
        115, "Aerospace Product and Parts Manufacturing", 3364
    )
    RAILROAD_ROLLING_STOCK_MANUFACTURING = LkIndustryCode(
        116, "Railroad Rolling Stock Manufacturing", 3365
    )
    SHIP_AND_BOAT_BUILDING = LkIndustryCode(117, "Ship and Boat Building", 3366)
    OTHER_TRANSPORTATION_EQUIPMENT_MANUFACTURING = LkIndustryCode(
        118, "Other Transportation Equipment Manufacturing", 3369
    )
    HOUSEHOLD_AND_INSTITUTIONAL_FURNITURE_AND_KITCHEN_CABINET_MANUFACTURING = LkIndustryCode(
        119, "Household and Institutional Furniture and Kitchen Cabinet Manufacturing", 3371
    )
    OTHER_FURNITURE_INCLUDING_FIXTURES_MANUFACTURING = LkIndustryCode(
        120, "Office Furniture (including Fixtures) Manufacturing", 3372
    )
    OTHER_FURNITURE_RELATED_PRODUCT_MANUFACTURING = LkIndustryCode(
        121, "Other Furniture Related Product Manufacturing", 3379
    )
    MEDICAL_EQUIPMENT_AND_SUPPLIES_MANUFACTURING = LkIndustryCode(
        122, "Medical Equipment and Supplies Manufacturing", 3391
    )
    OTHER_MISCELLANEOUS_MANUFACTURING = LkIndustryCode(
        123, "Other Miscellaneous Manufacturing", 3399
    )

    MOTOR_VEHICLE_AND_MOTOR_VEHICLE_PARTS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkIndustryCode(
        124, "Motor Vehicle and Motor Vehicle Parts and Supplies Merchant Wholesalers", 4231
    )
    FURNITURE_AND_HOME_FURNISHING_MERCHANT_WHOLESALERS = LkIndustryCode(
        125, "Furniture and Home Furnishing Merchant Wholesalers", 4232
    )
    LUMBER_AND_OTHER_CONSTRUCTION_MATERIALS_MERCHANT_WHOLESALERS = LkIndustryCode(
        126, "Lumber and Other Construction Materials Merchant Wholesalers", 4233
    )
    PROFESSIONAL_AND_COMMERCIAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkIndustryCode(
        127, "Professional and Commercial Equipment and Supplies Merchant Wholesalers", 4234
    )
    METAL_AND_MINERAL_EXCEPT_PETROLEUM_MERCHANT_WHOLESALERS = LkIndustryCode(
        128, "Metal and Mineral (except Petroleum) Merchant Wholesalers", 4235
    )
    HOUSEHOLD_APPLIANCES_AND_ELECTRICAL_AND_ELECTRONIC_GOODS_MERCHANT_WHOLESALERS = LkIndustryCode(
        129, "Household Appliances and Electrical and Electronic Goods Merchant Wholesalers", 4236
    )
    HARDWARE_AND_PLUMBING_AND_HEATING_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkIndustryCode(
        130, "Hardware, and Plumbing and Heating Equipment and Supplies Merchant Wholesalers", 4237
    )
    MACHINERY_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkIndustryCode(
        131, "Machinery, Equipment, and Supplies Merchant Wholesalers", 4238
    )
    MISCELLANEOUS_DURABLE_GOODS_MERCHANT_WHOLESALERS = LkIndustryCode(
        132, "Miscellaneous Durable Goods Merchant Wholesalers", 4239
    )
    PAPER_AND_PAPER_PRODUCT_MERCHANT_WHOLESALERS = LkIndustryCode(
        133, "Paper and Paper Product Merchant Wholesalers", 4241
    )
    DRUGS_AND_DRUGGISTS_SUNDRIES_MERCHANT_WHOLESALERS = LkIndustryCode(
        134, "Drugs and Druggists' Sundries Merchant Wholesalers", 4242
    )
    APPAREL_PIECE_GOODS_AND_NOTIONS_MERCHANT_WHOLESALERS = LkIndustryCode(
        135, "Apparel, Piece Goods, and Notions Merchant Wholesalers", 4243
    )
    GROCERY_AND_RELATED_PRODUCT_MERCHANT_WHOLESALERS = LkIndustryCode(
        136, "Grocery and Related Product Merchant Wholesalers", 4244
    )
    FARM_PRODUCT_RAW_MATERIAL_MERCHANT_WHOLESALERS = LkIndustryCode(
        137, "Farm Product Raw Material Merchant Wholesalers", 4245
    )
    CHEMICAL_AND_ALLIED_PRODUCTS_MERCHANT_WHOLESALERS = LkIndustryCode(
        138, "Chemical and Allied Products Merchant Wholesalers", 4246
    )
    PETROLEUM_AND_PETROLEUM_PRODUCTS_MERCHANT_WHOLESALERS = LkIndustryCode(
        139, "Petroleum and Petroleum Products Merchant Wholesalers", 4247
    )
    BEERS_WINE_AND_DISTILLED_ALCOHOLIC_BEVERAGE_MERCHANT_WHOLESALERS = LkIndustryCode(
        140, "Beer, Wine, and Distilled Alcoholic Beverage Merchant Wholesalers", 4248
    )
    MISCELLANEOUS_NONDURABLE_GOODS_MERCHANT_WHOLESALERS = LkIndustryCode(
        141, "Miscellaneous Nondurable Goods Merchant Wholesalers", 4249
    )
    WHOLESALE_ELECTRONIC_MARKETS_AND_AGENTS_AND_BROKERS = LkIndustryCode(
        142, "Wholesale Electronic Markets and Agents and Brokers", 4251
    )

    NEWSPAPER_PERIODICAL_BOOK_AND_DIRECTORY_PUBLISHERS = LkIndustryCode(
        143, "Newspaper, Periodical, Book, and Directory Publishers", 5111
    )
    SOFTWARE_PUBLISHERS = LkIndustryCode(144, "Software Publishers", 5112)
    MOTION_PICTURES_AND_VIDEO_INDUSTRIES = LkIndustryCode(
        145, "Motion Picture and Video Industries", 5121
    )
    SOUND_RECORDING_INDUSTRIES = LkIndustryCode(146, "Sound Recording Industries", 5122)
    RADIO_AND_TELEVISION_BROADCASTING = LkIndustryCode(
        147, "Radio and Television Broadcasting", 5151
    )
    CABLE_AND_OTHER_SUBSCRIPTION_PROGRAMMING = LkIndustryCode(
        148, "Cable and Other Subscription Programming", 5152
    )
    WIRED_AND_WIRELESS_TELECOMMUNICATIONS_CARRIERS = LkIndustryCode(
        149, "Wired and Wireless Telecommunications Carriers", 5173
    )
    SATELLITE_TELECOMMUNICATIONS = LkIndustryCode(150, "Satellite Telecommunications", 5174)
    OTHER_TELECOMMUNICATIONS = LkIndustryCode(151, "Other Telecommunications", 5179)
    DATA_PROCESSING_HOSTING_AND_RELATED_SERVICES = LkIndustryCode(
        152, "Data Processing, Hosting, and Related Services", 5182
    )
    OTHER_INFORMATION_SERVICES = LkIndustryCode(153, "Other Information Services", 5191)

    MONETARY_AUTHORITIES_CENTRAL_BANK = LkIndustryCode(
        154, "Monetary Authorities-Central Bank", 5211
    )
    DEPOSITORY_CREDIT_INTERMEDIATION = LkIndustryCode(155, "Depository Credit Intermediation", 5221)
    NON_DEPOSITORY_CREDIT_INTERMEDIATION = LkIndustryCode(
        156, "Nondepository Credit Intermediation", 5222
    )
    ACTIVITIES_RELATED_TO_CREDIT_INTERMEDIATION = LkIndustryCode(
        157, "Activities Related to Credit Intermediation", 5223
    )
    SECURITIES_AND_COMMODITY_CONTRACTS_INTERMEDIATION_AND_BROKERAGE = LkIndustryCode(
        158, "Securities and Commodity Contracts Intermediation and Brokerage", 5231
    )
    SECURITIES_AND_COMMODITY_EXCHANGES = LkIndustryCode(
        159, "Securities and Commodity Exchanges", 5232
    )
    OTHER_FINANCIAL_INVESTMENT_ACTIVITIES = LkIndustryCode(
        160, "Other Financial Investment Activities", 5239
    )
    INSURANCE_CARRIERS = LkIndustryCode(161, "Insurance Carriers", 5241)
    AGENCIES_BROKERAGES_AND_OTHER_INSURANCE_RELATED_ACTIVITIES = LkIndustryCode(
        162, "Agencies, Brokerages, and Other Insurance Related Activities", 5242
    )
    INSURANCE_AND_EMPLOYEE_BENEFIT_FUNDS = LkIndustryCode(
        163, "Insurance and Employee Benefit Funds", 5251
    )
    OTHER_INVESTMENT_POOLS_AND_FUNDS = LkIndustryCode(164, "Other Investment Pools and Funds", 5259)

    LESSORS_OF_REAL_ESTATE = LkIndustryCode(165, "Lessors of Real Estate", 5311)
    OFFICES_OF_REAL_ESTATE_AGENTS_BROKERS = LkIndustryCode(
        166, "Offices of Real Estate Agents and Brokers", 5312
    )
    ACTIVITIES_RELATED_TO_ESTATE = LkIndustryCode(167, "Activities Related to Real Estate", 5313)
    AUTOMOTIVE_EQUIPMENT_RENTAL_AND_LEASING = LkIndustryCode(
        168, "Automotive Equipment Rental and Leasing", 5321
    )
    CONSUMER_GOODS_RENTAL = LkIndustryCode(169, "Consumer Goods Rental", 5322)
    GENERAL_RENTAL_CENTERS = LkIndustryCode(170, "General Rental Centers", 5323)
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkIndustryCode(
        171, "Commercial and Industrial Machinery and Equipment Rental and Leasing", 5324
    )
    LESSORS_OF_NON_FINANCIAL_INTANGIBLE_ASSETS_EXCEPT_COPYRIGHTED_WORKS = LkIndustryCode(
        172, "Lessors of Nonfinancial Intangible Assets (except Copyrighted Works)", 5331
    )

    LEGAL_SERVICES = LkIndustryCode(173, "Legal Services", 5411)
    ACCOUNTING_TAX_PREPARATION_BOOKKEEPING_AND_PAYROLL_SERVICES = LkIndustryCode(
        174, "Accounting, Tax Preparation, Bookkeeping, and Payroll Services", 5412
    )
    ARCHITECTURAL_ENGINEERING_AND_RELATED_SERVICES = LkIndustryCode(
        175, "Architectural, Engineering, and Related Services", 5413
    )
    SPECIALIZED_DESIGN_SERVICES = LkIndustryCode(176, "Specialized Design Services", 5414)
    COMPUTER_SYSTEMS_DESIGN_AND_RELATED_SERVICES = LkIndustryCode(
        177, "Computer Systems Design and Related Services", 5415
    )
    MANAGEMENT_SCIENTIFIC_AND_TECHNICAL_CONSULTING_SERVICES = LkIndustryCode(
        178, "Management, Scientific, and Technical Consulting Services", 5416
    )
    SCIENTIFIC_RESEARCH_AND_DEVELOPMENT_SERVICES = LkIndustryCode(
        179, "Scientific Research and Development Services", 5417
    )
    ADVERTISING_PUBLIC_RELATIONS_AND_RELATED_SERVICES = LkIndustryCode(
        180, "Advertising, Public Relations, and Related Services", 5418
    )
    OTHER_PROFESSIONAL_SCIENTIFIC_AND_TECHNICAL_SERVICES = LkIndustryCode(
        181, "Other Professional, Scientific, and Technical Services", 5419
    )

    MANAGEMENT_OF_COMPANIES_AND_ENTERPRISES = LkIndustryCode(
        182, "Management of Companies and Enterprises", 5511
    )

    OTHER_ADMINISTRATIVE_SERVICES = LkIndustryCode(183, "Office Administrative Services", 5611)
    FACILITIES_SUPPORT_SERVICES = LkIndustryCode(184, "Facilities Support Services", 5612)
    EMPLOYMENT_SERVICES = LkIndustryCode(185, "Employment Services", 5613)
    BUSINESS_SUPPORT_SERVICES = LkIndustryCode(186, "Business Support Services", 5614)
    TRAVEL_ARRANGEMENT_AND_RESERVATION_SERVICES = LkIndustryCode(
        187, "Travel Arrangement and Reservation Services", 5615
    )
    INVESTIGATION_AND_SECURITY_SERVICES = LkIndustryCode(
        188, "Investigation and Security Services", 5616
    )
    SERVICES_TO_BUILDINGS_AND_DWELLINGS = LkIndustryCode(
        189, "Services to Buildings and Dwellings", 5617
    )
    OTHER_SUPPORT_SERVICES = LkIndustryCode(190, "Other Support Services", 5619)
    WASTE_COLLECTION = LkIndustryCode(191, "Waste Collection", 5621)
    WASTE_TREATMENT_AND_DISPOSAL = LkIndustryCode(192, "Waste Treatment and Disposal", 5622)
    REMEDIATION_AND_OTHER_WASTE_MANAGEMENT_SERVICES = LkIndustryCode(
        193, "Remediation and Other Waste Management Services", 5629
    )

    ELEMENTARY_AND_SECONDARY_SCHOOLS = LkIndustryCode(194, "Elementary and Secondary Schools", 6111)
    JUNIOR_COLLEGES = LkIndustryCode(195, "Junior Colleges", 6112)
    COLLEGES_UNIVERSITIES_AND_PROFESSIONAL_SCHOOLS = LkIndustryCode(
        196, "Colleges, Universities, and Professional Schools", 6113
    )
    BUSINESS_SCHOOLS_AND_COMPUTER_AND_MANAGEMENT_TRAINING = LkIndustryCode(
        197, "Business Schools and Computer and Management Training", 6114
    )
    TECHNICAL_AND_TRADE_SCHOOLS = LkIndustryCode(198, "Technical and Trade Schools", 6115)
    OTHER_SCHOOL_AND_INSTRUCTION = LkIndustryCode(199, "Other Schools and Instruction", 6116)
    EDUCATIONAL_SUPPORT_SERVICES = LkIndustryCode(200, "Educational Support Services", 6117)

    OFFICES_OF_PHYSICIANS = LkIndustryCode(201, "Offices of Physicians", 6211)
    OFFICES_OF_DENTISTS = LkIndustryCode(202, "Offices of Dentists", 6212)
    OFFICES_OF_OTHER_HEALTH_PRACTITIONERS = LkIndustryCode(
        203, "Offices of Other Health Practitioners", 6213
    )
    OUTPATIENT_CARE_CENTERS = LkIndustryCode(204, "Outpatient Care Centers", 6214)
    MEDICAL_AND_DIAGNOSTIC_LABORATORIES = LkIndustryCode(
        205, "Medical and Diagnostic Laboratories", 6215
    )
    OTHER_AMBULATORY_HEALTH_CARE_SERVICES = LkIndustryCode(
        206, "Other Ambulatory Health Care Services", 6219
    )
    GENERAL_MEDICAL_AND_SURGICAL_HOSPITALS = LkIndustryCode(
        207, "General Medical and Surgical Hospitals", 6221
    )
    PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkIndustryCode(
        208, "Psychiatric and Substance Abuse Hospitals", 6222
    )
    SPECIALTY_EXCEPT_PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkIndustryCode(
        209, "Specialty (except Psychiatric and Substance Abuse) Hospitals", 6223
    )
    NURSING_CARE_FACILITIES_SKILLED_NURSING_FACILITIES = LkIndustryCode(
        210, "Nursing Care Facilities (Skilled Nursing Facilities)", 6231
    )
    RESIDENTIAL_INTELLECTUAL_AND_DEVELOPMENTAL_DISABILITY_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_FACILITIES = LkIndustryCode(
        211,
        "Residential Intellectual and Developmental Disability, Mental Health, and Substance Abuse Facilities",
        6232,
    )
    CONTINUING_CARE_RETIREMENT_COMMUNITIES_AND_ASSISTED_LIVING_FACILITIES_FOR_THE_ELDERLY = LkIndustryCode(
        212,
        "Continuing Care Retirement Communities and Assisted Living Facilities for the Elderly",
        6233,
    )
    OTHER_RESIDENTIAL_CARE_FACILITIES = LkIndustryCode(
        213, "Other Residential Care Facilities", 6239
    )
    INDIVIDUAL_AND_FAMILY_SERVICES = LkIndustryCode(214, "Individual and Family Services", 6241)
    COMMUNITY_FOOD_AND_HOUSING_AND_EMERGENCY_AND_OTHER_RELIEF_SERVICES = LkIndustryCode(
        215, "Community Food and Housing, and Emergency and Other Relief Services", 6242
    )
    VOCATIONAL_REHABILITATION_SERVICES = LkIndustryCode(
        216, "Vocational Rehabilitation Services", 6243
    )
    CHILD_DAY_CARE_SERVICES = LkIndustryCode(217, "Child Day Care Services", 6244)

    PERFORMING_ARTS_COMPANIES = LkIndustryCode(218, "Performing Arts Companies", 7111)
    SPECTATOR_SPORTS = LkIndustryCode(219, "Spectator Sports", 7112)
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS = LkIndustryCode(
        220, "Promoters of Performing Arts, Sports, and Similar Events", 7113
    )
    AGENTS_AND_MANAGERS_FOR_ARTISTS_ATHLETES_ENTERTAINERS_AND_OTHER_PUBLIC_FIGURES = LkIndustryCode(
        221,
        "Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures",
        7114,
    )
    INDEPENDENT_ARTISTS_WRITERS_AND_PERFORMERS = LkIndustryCode(
        222, "Independent Artists, Writers, and Performers", 7115
    )
    MUSEUMS_HISTORICAL_SITES_AND_SIMILAR_INSTITUTIONS = LkIndustryCode(
        223, "Museums, Historical Sites, and Similar Institutions", 7121
    )
    AMUSEMENT_PARKS_AND_ARCADES = LkIndustryCode(224, "Amusement Parks and Arcades", 7131)
    GAMBLING_INDUSTRIES = LkIndustryCode(225, "Gambling Industries", 7132)
    OTHER_AMUSEMENT_AND_RECREATION_INDUSTRIES = LkIndustryCode(
        226, "Other Amusement and Recreation Industries", 7139
    )

    TRAVELER_ACCOMMODATION = LkIndustryCode(227, "Traveler Accommodation", 7211)
    RECREATIONAL_VEHICLE_PARKS_AND_RECREATIONAL_CAMPS = LkIndustryCode(
        228, "RV (Recreational Vehicle) Parks and Recreational Camps", 7212
    )
    ROOMING_AND_BOARDING_HOUSES_DORMITORIES_AND_WORKERS_CAMPS = LkIndustryCode(
        229, "Rooming and Boarding Houses, Dormitories, and Workers' Camps", 77213
    )
    SPECIAL_FOOD_SERVICES = LkIndustryCode(230, "Special Food Services", 7223)
    DRINKING_PLACES_ALCOHOLIC_BEVERAGES = LkIndustryCode(
        231, "Drinking Places (Alcoholic Beverages)", 7224
    )
    RESTAURANTS_AND_OTHER_EATING_PLACES = LkIndustryCode(
        232, "Restaurants and Other Eating Places", 7225
    )

    AUTOMOTIVE_REPAIR_AND_MAINTENANCE = LkIndustryCode(
        233, "Automotive Repair and Maintenance", 8111
    )
    ELECTRONIC_AND_PRECISION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkIndustryCode(
        234, "Electronic and Precision Equipment Repair and Maintenance", 8112
    )
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_EXCEPT_AUTOMOTIVE_AND_ELECTRIC_REPAIR_AND_MAINTENANCE = LkIndustryCode(
        235,
        "Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance",
        8113,
    )
    PERSONAL_AND_HOUSEHOLD_GOODS_REPAIR_AND_MAINTENANCE = LkIndustryCode(
        236, "Personal and Household Goods Repair and Maintenance", 8114
    )
    PERSONAL_CARE_SERVICES = LkIndustryCode(237, "Personal Care Services", 8121)
    DEATH_CARE_SERVICES = LkIndustryCode(238, "Death Care Services", 8122)
    DRYCLEANING_AND_LAUNDRY_SERVICES = LkIndustryCode(239, "Drycleaning and Laundry Services", 8123)
    OTHER_PERSONAL_SERVICES = LkIndustryCode(240, "Other Personal Services", 8129)
    RELIGIOUS_ORGANIZATIONS = LkIndustryCode(241, "Religious Organizations", 8131)
    GRANTMAKING_AND_GIVING_SERVICES = LkIndustryCode(242, "Grantmaking and Giving Services", 8132)
    SOCIAL_ADVOCACY_ORGANIZATIONS = LkIndustryCode(243, "Social Advocacy Organizations", 8133)
    CIVIC_AND_SOCIAL_ORGANIZATIONS = LkIndustryCode(244, "Civic and Social Organizations", 8134)
    BUSINESS_PROFESSIONAL_LABOR_POLITICAL_AND_SIMILAR_ORGANIZATIONS = LkIndustryCode(
        245, "Business, Professional, Labor, Political, and Similar Organizations", 8139
    )
    PRIVATE_HOUSEHOLDS = LkIndustryCode(246, "Private Households", 8141)

    EXECUTIVE_LEGISLATIVE_AND_OTHER_GENERAL_GOVERNMENT_SUPPORT = LkIndustryCode(
        247, "Executive, Legislative, and Other General Government Support", 9211
    )
    JUSTICE_PUBLIC_ORDER_AND_SAFETY_ACTIVITIES = LkIndustryCode(
        248, "Justice, Public Order, and Safety Activities", 9221
    )
    ADMINISTRATION_OF_HUMAN_RESOURCE_PROGRAMS = LkIndustryCode(
        249, "Administration of Human Resource Programs", 9231
    )
    ADMINISTRATION_OF_ENVIRONMENTAL_QUALITY_PROGRAMS = LkIndustryCode(
        250, "Administration of Environmental Quality Programs", 9241
    )
    ADMINISTRATION_OF_HOUSING_PROGRAMS_URBAN_PLANNING_AND_COMMUNITY_DEVELOPMENT = LkIndustryCode(
        251, "Administration of Housing Programs, Urban Planning, and Community Development", 9251
    )
    ADMINISTRATION_OF_ECONOMIC_PROGRAMS = LkIndustryCode(
        252, "Administration of Economic Programs", 9261
    )
    SPACE_RESEARCH_AND_TECHNOLOGY = LkIndustryCode(253, "Space Research and Technology", 9271)
    NATIONAL_SECURITY_AND_INTERNATIONAL_AFFAIRS = LkIndustryCode(
        254, "National Security and International Affairs", 9281
    )


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    IndustryCode.sync_to_database(db_session)
    db_session.commit()
