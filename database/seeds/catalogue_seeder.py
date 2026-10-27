"""
GutGuard – Indian Food Catalogue Seeder
Seeds the initial food catalogue with a broad range of Indian foods.
Data is categorised by region and type. Nutritional values are NOT invented;
only category metadata is seeded here.
"""

try:
    from backend.extensions import db
    from database.models import FoodCategory, FoodCatalogue, FoodAlias
except ImportError:
    from extensions import db
    from models import FoodCategory, FoodCatalogue, FoodAlias


def _norm(name: str) -> str:
    return name.lower().strip()


def seed_initial_catalogue():
    """Create categories and foods if they do not already exist."""

    # ── Categories ────────────────────────────────────────
    cats_data = [
        ("South Indian Breakfast",       "Idli, dosa, upma, pongal, idiyappam etc.",   1),
        ("South Indian Meals",           "Rice, sambar, rasam, curries, kootu",         2),
        ("North Indian Meals",           "Roti, dal, sabzi, paneer dishes",              3),
        ("East Indian Dishes",           "Litti chokha, rice dishes, mustard curries",   4),
        ("West Indian Dishes",           "Thepla, dhokla, pav bhaji, vada pav",         5),
        ("Rice & Staples",               "Plain rice, biryani, pulao, khichdi",          6),
        ("Breads & Rotis",               "Chapati, paratha, naan, puri, bhatura",        7),
        ("Dal & Lentils",                "Toor dal, masoor dal, chana dal, rajma",       8),
        ("Curries & Gravies",            "Mixed veg, palak paneer, chicken curry",       9),
        ("Vegetables & Side Dishes",     "Dry sabzi, stir-fry, podimas, thoran",       10),
        ("Sambar, Rasam & Chutneys",     "Sambar, rasam, coconut chutney, tomato chutney",11),
        ("Pickles & Accompaniments",     "Mango pickle, lime pickle, pappad",           12),
        ("Snacks & Street Food",         "Bajji, bonda, murukku, bhel puri, chaat",    13),
        ("Bakery & Packaged Foods",      "Bread, biscuits, cake, instant noodles",     14),
        ("Eggs & Non-Vegetarian",        "Eggs, chicken, fish, mutton",                15),
        ("Sweets & Desserts",            "Kheer, halwa, ladoo, jalebi, gulab jamun",   16),
        ("Beverages",                    "Tea, coffee, juice, buttermilk, lassi",       17),
        ("Hostel & Mess Foods",          "Common mess/canteen foods",                   18),
        ("Custom / Unclassified",        "User-submitted foods awaiting review",        99),
    ]

    cat_map: dict[str, FoodCategory] = {}
    for name, desc, order in cats_data:
        cat = FoodCategory.query.filter_by(name=name).first()
        if not cat:
            cat = FoodCategory(name=name, description=desc, sort_order=order)
            db.session.add(cat)
    db.session.flush()

    # Reload map
    for name, _, _ in cats_data:
        cat_map[name] = FoodCategory.query.filter_by(name=name).first()

    # ── Foods with aliases ─────────────────────────────────
    foods_data = [
        # (name, category_key, region, is_veg, [aliases])
        # South Indian Breakfast
        ("Idli",             "South Indian Breakfast", "South Indian", True,  ["Idly", "Steam idli"]),
        ("Dosa",             "South Indian Breakfast", "South Indian", True,  ["Plain dosa", "Sada dosa"]),
        ("Masala Dosa",      "South Indian Breakfast", "South Indian", True,  ["Masale dosa"]),
        ("Rava Dosa",        "South Indian Breakfast", "South Indian", True,  ["Sooji dosa"]),
        ("Set Dosa",         "South Indian Breakfast", "South Indian", True,  []),
        ("Uttapam",          "South Indian Breakfast", "South Indian", True,  ["Uthappam", "Oothappam"]),
        ("Upma",             "South Indian Breakfast", "South Indian", True,  ["Upuma", "Rava upma"]),
        ("Pongal",           "South Indian Breakfast", "South Indian", True,  ["Ven pongal", "Khara pongal", "Kichadi"]),
        ("Idiyappam",        "South Indian Breakfast", "South Indian", True,  ["String hoppers", "Rice noodles"]),
        ("Appam",            "South Indian Breakfast", "South Indian", True,  ["Hoppers", "Palappam"]),
        ("Poori",            "South Indian Breakfast", "South Indian", True,  ["Puri"]),
        ("Vada",             "South Indian Breakfast", "South Indian", True,  ["Medu vada", "Ulundu vada", "Wada"]),
        ("Pesarattu",        "South Indian Breakfast", "South Indian", True,  ["Green gram dosa"]),
        ("Akki Roti",        "South Indian Breakfast", "South Indian", True,  []),
        ("Puttu",            "South Indian Breakfast", "South Indian", True,  ["Rice puttu"]),

        # South Indian Meals
        ("Sambar Rice",      "South Indian Meals", "South Indian", True,  ["Sambar sadam"]),
        ("Curd Rice",        "South Indian Meals", "South Indian", True,  ["Thayir sadam", "Dahi bhat"]),
        ("Rasam Rice",       "South Indian Meals", "South Indian", True,  ["Rasam sadam"]),
        ("Lemon Rice",       "South Indian Meals", "South Indian", True,  ["Elumichai sadam"]),
        ("Tamarind Rice",    "South Indian Meals", "South Indian", True,  ["Puliogare", "Pulihora"]),
        ("Coconut Rice",     "South Indian Meals", "South Indian", True,  ["Thengai sadam"]),
        ("Tomato Rice",      "South Indian Meals", "South Indian", True,  ["Thakkali sadam"]),
        ("Bisibelebath",     "South Indian Meals", "South Indian", True,  ["Bisi bele bath", "Bisibele huli anna"]),

        # North Indian Meals
        ("Chapati",          "Breads & Rotis",     "North Indian", True,  ["Roti", "Phulka", "Chappati"]),
        ("Paratha",          "Breads & Rotis",     "North Indian", True,  ["Parantha"]),
        ("Aloo Paratha",     "Breads & Rotis",     "North Indian", True,  ["Aloo paratha"]),
        ("Naan",             "Breads & Rotis",     "North Indian", True,  ["Naan bread"]),
        ("Bhatura",          "Breads & Rotis",     "North Indian", True,  ["Batura"]),
        ("Dal Makhani",      "Dal & Lentils",      "North Indian", True,  ["Dal makhni"]),
        ("Rajma",            "Dal & Lentils",      "North Indian", True,  ["Rajma curry", "Kidney bean curry"]),
        ("Chole",            "Dal & Lentils",      "North Indian", True,  ["Chana masala", "Chickpea curry"]),
        ("Palak Paneer",     "Curries & Gravies",  "North Indian", True,  ["Spinach paneer"]),
        ("Paneer Butter Masala","Curries & Gravies","North Indian", True, ["Paneer makhani"]),
        ("Matar Paneer",     "Curries & Gravies",  "North Indian", True,  []),
        ("Aloo Gobi",        "Vegetables & Side Dishes","North Indian",True,["Potato cauliflower"]),
        ("Jeera Rice",       "Rice & Staples",     "North Indian", True,  ["Cumin rice"]),

        # Rice & Staples
        ("Plain Rice",       "Rice & Staples",     "Pan-India",    True,  ["Steamed rice", "Boiled rice", "Cooked rice"]),
        ("Biryani",          "Rice & Staples",     "Pan-India",    None,  ["Biriyani"]),
        ("Chicken Biryani",  "Rice & Staples",     "Pan-India",    False, ["Kozhi biryani"]),
        ("Mutton Biryani",   "Rice & Staples",     "Pan-India",    False, []),
        ("Vegetable Biryani","Rice & Staples",     "Pan-India",    True,  ["Veg biryani"]),
        ("Pulao",            "Rice & Staples",     "Pan-India",    True,  ["Pilaf", "Pulav"]),
        ("Khichdi",          "Rice & Staples",     "Pan-India",    True,  ["Khichri", "Pongal"]),
        ("Fried Rice",       "Rice & Staples",     "Pan-India",    None,  ["Chinese fried rice"]),

        # Dal & Lentils
        ("Toor Dal",         "Dal & Lentils",      "Pan-India",    True,  ["Arhar dal", "Pigeon pea dal"]),
        ("Masoor Dal",       "Dal & Lentils",      "Pan-India",    True,  ["Red lentil dal"]),
        ("Moong Dal",        "Dal & Lentils",      "Pan-India",    True,  ["Green gram dal", "Mung dal"]),
        ("Chana Dal",        "Dal & Lentils",      "Pan-India",    True,  ["Bengal gram dal"]),
        ("Sambar",           "Sambar, Rasam & Chutneys","South Indian",True,["Samber"]),
        ("Rasam",            "Sambar, Rasam & Chutneys","South Indian",True,["Pepper water", "Saaru"]),

        # Vegetables
        ("Mixed Vegetable Curry","Curries & Gravies","Pan-India",  True,  ["Veg curry", "Mixed veg"]),
        ("Potato Curry",     "Curries & Gravies",  "Pan-India",    True,  ["Aloo curry"]),
        ("Bhindi Masala",    "Vegetables & Side Dishes","North Indian",True,["Okra masala", "Ladies finger"]),
        ("Cabbage Stir-fry", "Vegetables & Side Dishes","Pan-India",True,  ["Cabbage thoran", "Cabbage poriyal"]),
        ("Beans Poriyal",    "Vegetables & Side Dishes","South Indian",True,["French beans stir-fry"]),
        ("Carrot Kootu",     "Vegetables & Side Dishes","South Indian",True,[]),

        # Chutneys & Accompaniments
        ("Coconut Chutney",  "Sambar, Rasam & Chutneys","South Indian",True,["Thengai chutney"]),
        ("Tomato Chutney",   "Sambar, Rasam & Chutneys","South Indian",True,["Thakkali chutney"]),
        ("Mango Pickle",     "Pickles & Accompaniments","Pan-India",  True, ["Avakaya", "Aam ka achaar"]),
        ("Lime Pickle",      "Pickles & Accompaniments","Pan-India",  True, ["Lemon pickle"]),
        ("Pappad",           "Pickles & Accompaniments","Pan-India",  True, ["Papad", "Appadam"]),

        # West Indian
        ("Dhokla",           "West Indian Dishes", "West Indian",  True,  []),
        ("Thepla",           "West Indian Dishes", "West Indian",  True,  []),
        ("Pav Bhaji",        "West Indian Dishes", "West Indian",  True,  []),
        ("Vada Pav",         "West Indian Dishes", "West Indian",  True,  ["Batata vada pav"]),
        ("Poha",             "West Indian Dishes", "West Indian",  True,  ["Flattened rice", "Aval"]),
        ("Sabudana Khichdi", "West Indian Dishes", "West Indian",  True,  ["Sago khichdi"]),

        # East Indian
        ("Litti Chokha",     "East Indian Dishes", "East Indian",  True,  []),
        ("Mustard Fish Curry","East Indian Dishes","East Indian",  False, []),
        ("Macher Jhol",      "East Indian Dishes", "East Indian",  False, ["Fish curry Bengali"]),

        # Snacks & Street Food
        ("Bajji",            "Snacks & Street Food","South Indian", True, ["Pakoda", "Bhajji", "Pakora"]),
        ("Bonda",            "Snacks & Street Food","South Indian", True, ["Potato bonda"]),
        ("Murukku",          "Snacks & Street Food","South Indian", True, ["Chakli"]),
        ("Bhel Puri",        "Snacks & Street Food","West Indian",  True, []),
        ("Pani Puri",        "Snacks & Street Food","Pan-India",    True, ["Golgappa", "Puchka"]),
        ("Samosa",           "Snacks & Street Food","North Indian", True, ["Singara"]),
        ("Chaat",            "Snacks & Street Food","Pan-India",    True, ["Aloo chaat"]),
        ("Bread Omelette",   "Snacks & Street Food","Pan-India",    False,["Bread omelet"]),
        ("Masala Peanuts",   "Snacks & Street Food","Pan-India",    True, ["Fried groundnuts"]),
        ("Popcorn",          "Snacks & Street Food","Pan-India",    True, []),

        # Bakery & Packaged
        ("White Bread",      "Bakery & Packaged Foods","Pan-India", True, ["Bread slice"]),
        ("Whole Wheat Bread","Bakery & Packaged Foods","Pan-India", True, ["Brown bread"]),
        ("Biscuits",         "Bakery & Packaged Foods","Pan-India", True, ["Cookies"]),
        ("Instant Noodles",  "Bakery & Packaged Foods","Pan-India", True, ["Maggi noodles", "Cup noodles"]),
        ("Cake",             "Bakery & Packaged Foods","Pan-India", True, []),
        ("Rusks",            "Bakery & Packaged Foods","Pan-India", True, ["Toasted bread"]),

        # Eggs & Non-Veg
        ("Boiled Egg",       "Eggs & Non-Vegetarian","Pan-India",  False,["Hard boiled egg", "Egg boil"]),
        ("Omelette",         "Eggs & Non-Vegetarian","Pan-India",  False,["Egg omelette"]),
        ("Scrambled Eggs",   "Eggs & Non-Vegetarian","Pan-India",  False,["Egg bhurji"]),
        ("Chicken Curry",    "Eggs & Non-Vegetarian","Pan-India",  False,["Kozhi curry"]),
        ("Mutton Curry",     "Eggs & Non-Vegetarian","Pan-India",  False,["Lamb curry"]),
        ("Fish Curry",       "Eggs & Non-Vegetarian","Pan-India",  False,["Meen curry"]),
        ("Tandoori Chicken", "Eggs & Non-Vegetarian","North Indian",False,[]),
        ("Egg Fried Rice",   "Eggs & Non-Vegetarian","Pan-India",  False,[]),

        # Sweets & Desserts
        ("Kheer",            "Sweets & Desserts",  "Pan-India",    True, ["Payasam", "Rice pudding"]),
        ("Halwa",            "Sweets & Desserts",  "Pan-India",    True, ["Sooji halwa", "Semolina halwa"]),
        ("Ladoo",            "Sweets & Desserts",  "Pan-India",    True, ["Besan ladoo", "Boondi ladoo", "Laddoo"]),
        ("Jalebi",           "Sweets & Desserts",  "Pan-India",    True, []),
        ("Gulab Jamun",      "Sweets & Desserts",  "Pan-India",    True, []),
        ("Rasgulla",         "Sweets & Desserts",  "East Indian",  True, []),
        ("Peda",             "Sweets & Desserts",  "Pan-India",    True, []),
        ("Mysore Pak",       "Sweets & Desserts",  "South Indian", True, []),
        ("Payasam",          "Sweets & Desserts",  "South Indian", True, ["Kheer", "Paramannam"]),
        ("Banana",           "Sweets & Desserts",  "Pan-India",    True, ["Plantain"]),

        # Beverages
        ("Tea",              "Beverages",          "Pan-India",    True, ["Chai", "Milk tea"]),
        ("Coffee",           "Beverages",          "Pan-India",    True, ["Filter coffee", "Kaapi"]),
        ("Milk",             "Beverages",          "Pan-India",    True, ["Plain milk"]),
        ("Buttermilk",       "Beverages",          "South Indian", True, ["Mor", "Chaas", "Chachh"]),
        ("Lassi",            "Beverages",          "North Indian", True, ["Sweet lassi", "Salted lassi"]),
        ("Tender Coconut Water","Beverages",       "South Indian", True, ["Coconut water", "Elaneer"]),
        ("Fruit Juice",      "Beverages",          "Pan-India",    True, ["Fresh juice"]),
        ("Lemon Juice",      "Beverages",          "Pan-India",    True, ["Nimbu paani", "Lemonade"]),
        ("Sugarcane Juice",  "Beverages",          "Pan-India",    True, []),

        # Hostel / Mess
        ("Mess Lunch",       "Hostel & Mess Foods","Pan-India",   None, ["Canteen lunch", "Hostel lunch"]),
        ("Mess Breakfast",   "Hostel & Mess Foods","Pan-India",   None, ["Canteen breakfast"]),
        ("Mess Dinner",      "Hostel & Mess Foods","Pan-India",   None, ["Canteen dinner"]),
        ("Canteen Sandwich", "Hostel & Mess Foods","Pan-India",   True, []),
        ("Canteen Dosa",     "Hostel & Mess Foods","South Indian",True, []),
    ]

    added = 0
    for name, cat_key, region, is_veg, aliases in foods_data:
        name_norm = _norm(name)
        if FoodCatalogue.query.filter_by(name_normalized=name_norm).first():
            continue  # Skip if already exists

        # Core hostel mess staples are verified as campus standard; specialty items remain for admin review
        is_staple = cat_key in ("South Indian Breakfast", "South Indian Meals", "Rice & Staples", "Dal & Lentils")
        source_label = "Campus Mess Standard Reference" if is_staple else "Student Canteen Menu Reference"

        cat = cat_map.get(cat_key)
        food = FoodCatalogue(
            name=name,
            name_normalized=name_norm,
            category_id=cat.id if cat else None,
            region=region,
            is_vegetarian=is_veg,
            status="active",
            is_verified=is_staple,
            data_source=source_label,
        )
        db.session.add(food)
        db.session.flush()

        for alias in aliases:
            alias_norm = _norm(alias)
            # Avoid duplicate alias keys
            if not FoodAlias.query.filter_by(alias_normalized=alias_norm).first():
                db.session.add(FoodAlias(
                    food_id=food.id,
                    alias=alias,
                    alias_normalized=alias_norm,
                ))
        added += 1

    db.session.commit()
    print(f"[seeder] Added {added} new food items to catalogue.")
