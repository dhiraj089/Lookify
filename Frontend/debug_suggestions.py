
import os
import csv
import random
import json

# Mocking the environment
BASE_DIR = r"d:\Lookify\Frontend"

def test_suggestions(seed_name=''):
    print(f"Testing with seed: '{seed_name}'", flush=True)
    try:
        # Read styles.csv
        csv_path = os.path.join(os.path.dirname(BASE_DIR), 'styles.csv')
        if not os.path.exists(csv_path):
             csv_path = os.path.join(BASE_DIR, 'styles.csv')
        
        print(f"CSV Path: {csv_path}", flush=True)

        items = []
        
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                print(f"Rows found: {len(all_rows)}")
        
                seed_item = None
                if seed_name:
                    for row in all_rows:
                        if seed_name.strip().lower() in row['productDisplayName'].strip().lower():
                            seed_item = row
                            break
                
                # --- SMART SEED PARSING ---
                if not seed_item:
                    seed_lower = seed_name.lower()
                    
                    # Guess Gender
                    guessed_gender = 'Men' # Default
                    
                    women_keywords = ['women', 'girl', 'dress', 'skirt', 'saree', 'lehenga', 'kurti', 'gown', 'top', 'blouse', 'legging', 'churidar']
                    men_keywords = ['men', 'boy', 'shirt', 'tshirt', 'trouser', 'suit', 'sherwani']
                    
                    # Check for women first (prioritize 'top' as women's if ambiguous, though 'tank top' could be men)
                    if any(x in seed_lower for x in women_keywords): 
                        guessed_gender = 'Women'
                    elif any(x in seed_lower for x in men_keywords):
                        guessed_gender = 'Men'
                    
                    # Guess Category
                    guessed_sub_cat = 'Topwear' # Default
                    if any(x in seed_lower for x in ['jeans', 'trousers', 'pant', 'shorts', 'skirt', 'leggings']):
                        guessed_sub_cat = 'Bottomwear'
                    elif any(x in seed_lower for x in ['shoe', 'sandal', 'heel', 'flat', 'boot', 'sneaker']):
                        guessed_sub_cat = 'Shoes'
                        
                    seed_item = {
                        'gender': guessed_gender,
                        'masterCategory': 'Apparel' if guessed_sub_cat != 'Shoes' else 'Footwear',
                        'subCategory': guessed_sub_cat,
                        'articleType': 'Unknown',
                        'usage': 'Casual'
                    }

                # --- STRICT SETTINGS ---
                gender = seed_item['gender']
                print(f"DEBUG: Seed='{seed_name}', Detected Gender='{gender}'", flush=True)

                master_cat = seed_item['masterCategory']
                sub_cat = seed_item['subCategory']
                
                print(f"Gender: {gender}, SubCat: {sub_cat}", flush=True)

                # Normalize Gender for strict filtering
                target_gender_group = []
                if gender in ['Men', 'Boys']:
                    target_gender_group = ['Men', 'Boys'] 
                    target_gender_group.append('Unisex') 
                elif gender in ['Women', 'Girls']:
                    target_gender_group = ['Women', 'Girls'] # STRICT: "Women things only" requested. Excludes Unisex.
                else: 
                    target_gender_group = ['Men', 'Boys', 'Unisex'] # Default fallback
                    
                # Strict Categories
                MEN_BOTTOMS = ['Jeans', 'Trousers', 'Track Pants', 'Shorts', 'Tracksuits'] 
                MEN_TOPS = ['Tshirts', 'Shirts', 'Sweatshirts', 'Kurtas', 'Jackets']
                MEN_SHOES = ['Casual Shoes', 'Sports Shoes', 'Formal Shoes', 'Sandals', 'Flip Flops']
                MEN_WATCHES = ['Watches']
                MEN_ACCESSORIES = ['Belts', 'Wallets'] 
                
                WOMEN_BOTTOMS = ['Jeans', 'Trousers', 'Leggings', 'Capris', 'Shorts', 'Skirts', 'Jeggings', 'Track Pants', 'Churidar', 'Salwar']
                WOMEN_TOPS = ['Tops', 'Tshirts', 'Shirts', 'Kurtas', 'Tunics', 'Sweatshirts']
                WOMEN_SHOES = ['Heels', 'Flats', 'Casual Shoes', 'Sports Shoes', 'Sandals']
                WOMEN_WATCHES = ['Watches']
                WOMEN_BAGS = ['Handbags', 'Clutches'] # Priority 1
                WOMEN_ACCESSORIES = ['Belts', 'Wallets'] # Priority 2
                
                # --- PRE-FILTER CANDIDATES ---
                candidates = {
                    'tops': [],
                    'bottoms': [],
                    'shoes': [],
                    'watches': [],
                    'accessories': [],
                    'bags': []
                }
                
                for row in all_rows:
                    # 1. Strict Filter
                    if row['gender'] not in target_gender_group:
                        continue
                        
                    # 2. Strict Category Map
                    rtype = row['articleType']
                    
                    if gender in ['Men', 'Boys']:
                        if rtype in MEN_TOPS: candidates['tops'].append(row)
                        elif rtype in MEN_BOTTOMS: candidates['bottoms'].append(row)
                        elif rtype in MEN_SHOES: candidates['shoes'].append(row)
                        elif rtype in MEN_WATCHES: candidates['watches'].append(row)
                        elif rtype in MEN_ACCESSORIES: candidates['accessories'].append(row)
                    else:
                        if rtype in WOMEN_TOPS: candidates['tops'].append(row)
                        elif rtype in WOMEN_BOTTOMS: candidates['bottoms'].append(row)
                        elif rtype in WOMEN_SHOES: candidates['shoes'].append(row)
                        elif rtype in WOMEN_WATCHES: candidates['watches'].append(row)
                        elif rtype in WOMEN_BAGS: candidates['bags'].append(row)
                        elif rtype in WOMEN_ACCESSORIES: candidates['accessories'].append(row)
                
                print(f"Candidates found: Tops={len(candidates['tops'])}, Bottoms={len(candidates['bottoms'])}, Shoes={len(candidates['shoes'])}, Watches={len(candidates['watches'])}, Bags={len(candidates['bags'])}, Acc={len(candidates['accessories'])}", flush=True)
                
                # Check specifics for Women
                if gender == 'Women':
                     print("Sample Bags:", [x['productDisplayName'] for x in candidates['bags'][:3]], flush=True)

                # --- SELECT 4 ITEMS ---
                final_selection = []
                
                def get_random(key):
                    if candidates.get(key):
                        return random.choice(candidates[key])
                    return None

                # Slot 1: Complementary Apparel 
                slot1 = None
                if sub_cat == 'Topwear':
                    slot1 = get_random('bottoms') 
                elif sub_cat == 'Bottomwear':
                    slot1 = get_random('tops') 
                else: 
                     # For Shoes/Accessories/Etc, suggest clothing based on gender
                     if gender in ['Men', 'Boys']: slot1 = get_random('tops')
                     else: slot1 = get_random('tops') # Default to top or dress
                
                if slot1: final_selection.append({'slot': 'Bottom/Top', 'item': slot1})
                
                # Slot 2: Shares
                slot2 = get_random('shoes')
                if slot2: final_selection.append({'slot': 'Shoes', 'item': slot2})
                
                # Slot 3: Watch
                slot3 = get_random('watches')
                if slot3: final_selection.append({'slot': 'Watch', 'item': slot3})
                
                # Slot 4: Accessories
                slot4 = None
                if gender in ['Women', 'Girls']:
                     # Try Bags first
                     slot4 = get_random('bags')
                     if not slot4: slot4 = get_random('accessories')
                else:
                     slot4 = get_random('accessories')

                if slot4: final_selection.append({'slot': 'Accessory', 'item': slot4})
                
                # Fallback
                if len(final_selection) < 4:
                    all_remaining = []
                    for k in candidates:
                        all_remaining.extend(candidates[k])
                    random.shuffle(all_remaining)
                    
                    for item in all_remaining:
                        if len(final_selection) >= 4: break
                        # Check existence (using ID)
                        exists = False
                        for fs in final_selection:
                            if fs['item']['id'] == item['id']: exists = True
                        if not exists:
                            final_selection.append({'slot': 'Filler', 'item': item})

                # Print Final
                print("-" * 20, flush=True)
                print(f"Final Selection for {seed_name} ({gender}):", flush=True)
                for fs in final_selection:
                    i = fs['item']
                    print(f"[{fs['slot']}] {i['articleType']} ({i['gender']}): {i['productDisplayName']}", flush=True)
                print("-" * 20, flush=True)

                return final_selection

    except Exception as e:
        print(f"CRASH: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # test_suggestions('Mens Tshirt')
    # print("\n\n", flush=True)
    # test_suggestions('Womens Top')
    print("\n\n", flush=True)
    test_suggestions('Pink Top') # Ambiguous case


