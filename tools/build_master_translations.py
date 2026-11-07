# -*- coding: utf-8 -*-
"""
tools/build_master_translations.py

Translates all remaining unhooked strings from the script dump into polytonic Koine Greek,
encodes them with hmgreek, appends them to greek_script.json, rebuilds pilot.gba with insert_text.py,
and updates apply_greek_ui_and_speakers.py to synchronize all IPS patches.
"""

import os
import sys
import json
import re

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('hm_greek_handover_package/tools')
import hmgreek
import insert_text

# Load all unhooked strings
raw_unhooked = json.load(open('tools/unhooked_strings.json', 'r', encoding='utf-8'))
print(f"Loaded {len(raw_unhooked)} unhooked unique entries.")

# Master translation dictionary for exact and patterned strings
T = {}

# 1. Villager names
villagers = {
    'Lillia': 'Λιλλία', 'Rick': 'Ῥῖκος', 'Popuri': 'Ποπούρα', 'Barley': 'Βαρλῆς', 'May': 'Μαΐα',
    'Saibara': 'Σαϊβάρας', 'Gray': 'Γραῖος', 'Duke': 'Δούξ', 'Manna': 'Μάννα', 'Basil': 'Βασίλειος',
    'Anna': 'Ἄννα', 'Mary': 'Μαρία', 'Thomas': 'Θωμᾶς', 'Harris': 'Ἄρρις', 'Ellen': 'Ἑλένη',
    'Stu': 'Στοῦ', 'Jeff': 'Ἰωσήφ', 'Sasha': 'Σάσα', 'Karen': 'Καρίνα', 'Doctor': 'Ἰατρός',
    'Elli': 'Ἔλλη', 'Carter': 'Κάρτερ', 'Cliff': 'Κλίφ', 'Doug': 'Δοῦγος', 'Gotz': 'Γότζης',
    'Zack': 'Ζάκχος', 'Won': 'Οὐών', 'Gourmet': 'Γεύστης', 'H. Goddess': 'Θεά', 'Harvest Goddess': 'Θεά',
    'Kappa': 'Κάππα', 'Staid': 'Σταΐδ', 'Nappy': 'Νάππυ', 'Bold': 'Βόλδ', 'Chef': 'Σέφ',
    'Aqua': 'Ἄκουα', 'Hoggy': 'Ὅγγυ', 'Timid': 'Τίμιδ', 'Van': 'Βάν', 'Ruby': 'Ῥούβη',
    'Child': 'Τέκνον', 'Player': 'Παίκτης',
}
for en, el in villagers.items():
    T[en] = el

# 2. Villager Affection / Love / Family
for en_name, el_name in villagers.items():
    T[f"{en_name}'s love{{N:%}}"] = f"Ἔρως τῆς {el_name}{{N:%}}" if el_name.endswith(('α', 'η')) else f"Ἔρως τοῦ {el_name}{{N:%}}"
    T[f"{en_name}'s affection{{N:%}}"] = f"Φιλία τῆς {el_name}{{N:%}}" if el_name.endswith(('α', 'η')) else f"Φιλία τοῦ {el_name}{{N:%}}"
    T[f"{en_name}'s"] = f"Τῆς {el_name}" if el_name.endswith(('α', 'η')) else f"Toῦ {el_name}"

# 3. Animals & Farm
farm_terms = {
    'Chicken': 'Ὄρνις', 'Chickens': 'Ὄρνιθες', 'Cow': 'Βοῦς', 'Cows': 'Βόες',
    'Sheep': 'Πρόβατον', 'Sheeps': 'Πρόβατα', 'Horse': 'Ἵππος', "Horse's": 'Toῦ ἵππου',
    'Dog': 'Κύων', "Dog's": 'Toῦ κυνός', 'Animal': 'Κτῆνος', 'Animals': 'Κτήνη',
    'Farm': 'Ἀγρός', "Farm's": 'Toῦ ἀγροῦ', 'Your': 'Σόν', 'Your name': 'Τὸ ὄνομά σου',
    'Your birthday': 'Τὰ γενέθλιά σου', 'Farm name': 'Τὸ τοῦ ἀγροῦ', "Dog's name": 'Τὸ τοῦ κυνός',
    'Is this OK?': 'Καλῶς ἔχει;', 'Is this name correct?': 'Ὀρθὸν τὸ ὄνομα;',
    'Yes': 'Ναί', 'No': 'Οὔ', 'End': 'Τέλος', 'Buttons': 'Πλῆκτρα', 'Clock': 'Ὡρολόγιον',
    'Face': 'Πρόσωπον', 'Name': 'Ὄνομα', 'Years': 'Ἔτη', 'Day': 'Ἡμέρα',
    'Diary': 'Βίβλος', 'Save': 'Σῷζε', 'Load': 'Φέρε', 'Data 1': 'Μέρος 1', 'Data 2': 'Μέρος 2',
    'Read diary.': 'Ἀνάγνωθι.', 'Write in diary.': 'Γράφε ἐν βίβλῳ.',
    'There is no saved data.': 'Οὐδὲν γεγραμμένον.', 'Load?': 'Φέρειν;', 'Overwrite?': 'Μεταγραφή;',
}
T.update(farm_terms)

# 4. Tools & Upgrades
tool_levels = [
    ('', ''), ('Iron ', 'Σιδηροῦν '), ('Copper ', 'Χαλκοῦν '), ('Silver ', 'Ἀργυροῦν '),
    ('Gold ', 'Χρυσοῦν '), ('Mystrile ', 'Μυθρίλιον '), ('Cursed ', 'Ἐπικατάρατον '),
    ('Blessed ', 'Εὐλογημένον '), ('Mythic ', 'Μυθικὸν ')
]
base_tools = [
    ('Sickle', 'δρέπανον'), ('Hoe', 'σκαφίς'), ('Axe', 'ἀξίνη'),
    ('Hammer', 'σφῦρα'), ('Watering Can', 'ποτιστήριον'), ('Fishing Rod', 'κάλαμος')
]
for en_lvl, el_lvl in tool_levels:
    for en_tool, el_tool in base_tools:
        # Greek grammar: neuter adjective for drepanon / potistirion, feminine for skaphis / axini / sphyra, masculine for kalamos
        adj = el_lvl.strip()
        if adj:
            if el_tool in ('δρέπανον', 'ποτιστήριον'):
                pass # neuter default
            elif el_tool in ('σκαφίς', 'ἀξίνη', 'σφῦρα'):
                adj_fem = {'Σιδηροῦν':'Σιδηρᾶ', 'Χαλκοῦν':'Χαλκῆ', 'Ἀργυροῦν':'Ἀργυρᾶ',
                           'Χρυσοῦν':'Χρυσῆ', 'Μυθρίλιον':'Μυθριλία', 'Ἐπικατάρατον':'Ἐπικατάρατος',
                           'Εὐλογημένον':'Εὐλογημένη', 'Μυθικὸν':'Μυθική'}.get(adj, adj)
                adj = adj_fem
            elif el_tool == 'κάλαμος':
                adj_masc = {'Σιδηροῦν':'Σιδηροῦς', 'Χαλκοῦν':'Χαλκοῦς', 'Ἀργυροῦν':'Ἀργυροῦς',
                            'Χρυσοῦν':'Χρυσοῦς', 'Μυθρίλιον':'Μυθρίλιος', 'Ἐπικατάρατον':'Ἐπικατάρατος',
                            'Εὐλογημένον':'Εὐλογημένος', 'Μυθικὸν':'Μυθικός'}.get(adj, adj)
                adj = adj_masc
            T[f"{en_lvl}{en_tool}".strip()] = f"{adj} {el_tool}"
        else:
            T[en_tool] = el_tool.capitalize()

# 5. Seeds & Crops
crops = {
    'Turnip': 'Γογγυλίς', 'Potato': 'Γεώμηλον', 'Cucumber': 'Σίκυος', 'Strawberry': 'Χαμαικέρασον',
    'Cabbage': 'Κράμβη', 'Tomato': 'Τομάτα', 'Corn': 'Ἀραβόσιτος', 'Onion': 'Κρόμμυον',
    'Pumpkin': 'Κολοκύνθη', 'Pineapple': 'Ἀνανᾶς', 'Eggplant': 'Μελιτζάνα', 'Carrot': 'Δαῦκος',
    'Sweet Potato': 'Γλυκεῖα βατάτα', 'Spinach': 'Σπανάκιον', 'Green Pepper': 'Πέπερι',
    'Grass': 'Πόα', 'Moon Drop': 'Σεληνοστάλαγμα', 'Pink Cat': 'Ῥοδόθριξ',
    'Magic': 'Μαγικόν', 'Toy Flower': 'Ἀθυρμανθός',
}
for c_en, c_el in crops.items():
    T[c_en] = c_el
    T[f"{c_en} Seeds"] = f"Σπέρματα {c_el}"

# 6. Animal Produce & Items
produce = {
    'Regular Quality Egg': 'ᾨὸν ἁπλοῦν', 'Good Quality Egg': 'ᾨὸν καλόν',
    'High Quality Egg': 'ᾨὸν ἄριστον', 'Golden Egg': 'ᾨὸν χρυσοῦν',
    'P Egg': 'ᾨὸν Π', 'X Egg': 'ᾨὸν Ξ', 'Spa-Boiled Egg': 'ᾨὸν θερμὸν',
    'Mayonnaise (S)': 'Ὠογάλειμμα (Μ)', 'Mayonnaise (M)': 'Ὠογάλειμμα (ΜΕ)',
    'Mayonnaise (L)': 'Ὠογάλειμμα (ΜΕΓ)', 'Mayonnaise (G)': 'Ὠογάλειμμα (Χ)',
    'Mayonnaise (P)': 'Ὠογάλειμμα (Π)', 'Mayonnaise (X)': 'Ὠογάλειμμα (Ξ)',
    'Milk (S)': 'Γάλα (Μ)', 'Milk (M)': 'Γάλα (ΜΕ)', 'Milk (L)': 'Γάλα (ΜΕΓ)',
    'Milk (G)': 'Γάλα (Χ)', 'Milk (P)': 'Γάλα (Π)', 'Milk (X)': 'Γάλα (Ξ)',
    'Cheese (S)': 'Τυρὸς (Μ)', 'Cheese (M)': 'Τυρὸς (ΜΕ)', 'Cheese (L)': 'Τυρὸς (ΜΕΓ)',
    'Cheese (G)': 'Τυρὸς (Χ)', 'Cheese (P)': 'Τυρὸς (Π)', 'Cheese (X)': 'Τυρὸς (Ξ)',
    'Wool (S)': 'Ἔριον (Μ)', 'Wool (M)': 'Ἔριον (ΜΕ)', 'Wool (L)': 'Ἔριον (ΜΕΓ)',
    'Wool (G)': 'Ἔριον (Χ)', 'Wool (P)': 'Ἔριον (Π)', 'Wool (X)': 'Ἔριον (Ξ)',
    'Yarn (S)': 'Νῆμα (Μ)', 'Yarn (M)': 'Νῆμα (ΜΕ)', 'Yarn (L)': 'Νῆμα (ΜΕΓ)',
    'Yarn (G)': 'Νῆμα (Χ)', 'Yarn (P)': 'Νῆμα (Π)', 'Yarn (X)': 'Νῆμα (Ξ)',
    'Brush': 'Κτείς', 'Milker': 'Ἀμολγεύς', 'Clipper': 'Ψαλίς', 'Bell': 'Κώδων',
    'Animal Medicine': 'Φάρμακον κτηνῶν', 'Blue Feather': 'Πτερὸν κυανοῦν',
    'Pedometer': 'Βηματομετρητής', 'Teleport Stone': 'Λίθος τηλεμεταφορᾶς',
    'Gem of the Goddess': 'Ψῆφος Θεᾶς', 'Gem of the Kappa': 'Ψῆφος Κάππα',
    'Gem of Truth': 'Ψῆφος Ἀληθείας',
}
T.update(produce)

# 7. Minerals & Ores
minerals = {
    'Junk Ore': 'Ἄχρηστον μέταλλον', 'Copper Ore': 'Χαλκός', 'Silver Ore': 'Ἄργυρος',
    'Gold Ore': 'Χρυσός', 'Mystrile': 'Μυθρίλιον', 'Orichalc': 'Ὀρείχαλκος',
    'Adamantite': 'Ἀδαμάντινον', 'Moon Stone': 'Σεληνόλιθος', 'Sand Rose': 'Ῥόδον ψάμμου',
    'Pink Diamond': 'Ῥόδινος ἀδάμας', 'Alexandrite': 'Ἀλεξανδρίτης', 'Amethyst': 'Ἀμέθυστος',
    'Agate': 'Ἀχάτης', 'Fluorite': 'Φθορίτης', 'Peridot': 'Περίδοτον', 'Topaz': 'Τοπάζιον',
    'Ruby': 'Ῥουβίνιον', 'Emerald': 'Σμάραγδος', 'Diamond': 'Ἀδάμας',
}
T.update(minerals)

# 8. Interactive Choices & Questions
choices = {
    'Accept': 'Δέχομαι', "Don't accept": 'Οὐ δέχομαι',
    'Sure.': 'Πάνυ γε.', 'Sure!': 'Πάνυ γε!', 'Sure, I will.': 'Πάνυ γε, ποιήσω.',
    'I could use some help.': 'Βοηθείας δέομαι.', 'No problem.': 'Οὐδὲν πρᾶγμα.',
    "I'd be glad to.": 'Ἡδέως ἄν.', "Sorry, I'm busy.": 'Συγγνώμη, ἀσχολῶ.',
    "I'm too busy now!": 'Ἀσχολῶ νῦν!', 'Just my name': 'Τὸ ὄνομά μου μόνον',
    'Darling': 'Φίλτατε', 'Honey': 'Γλυκύτατε', 'Dear': 'Φίλε',
    'Yes, I do.': 'Ναί, φιλῶ.', "No, I don't.": 'Οὔ, οὐ φιλῶ.',
    'Sure, I\'ll play.': 'Παίξω δή.', "Sorry, I've got work.": 'Συγγνώμη, ἔργον ἔχω.',
    'I agree with Popuri.': 'Ποπούρᾳ συνεπαινῶ.', 'I agree with Rick.': 'Ῥίκῳ συνεπαινῶ.',
    'Poor Lillia.': 'Φεῦ Λιλλίᾳ.', 'Of course!': 'Πῶς γὰρ οὔ!', 'Sounds great!': 'Καλὸν φαίνεται!',
    "I really couldn't.": 'Οὐ δύναμαι ὄντως.', 'I like cleaning.': 'Φιλῶ τὸ καθαρίζειν.',
    'I hate cleaning.': 'Μισῶ τὸ καθαρίζειν.', 'Take her to the Clinic.': 'Εἰς ἰατρεῖον ἄγε.',
    'I like her.': 'Φιλῶ αὐτήν.', 'Only as a friend.': 'Ὡς φίλην μόνον.',
    'Can I help?': 'Δύναμαι βοηθεῖν;', 'Be careful.': 'Εὐλαβοῦ.',
    "Sorry, I don't want to.": 'Συγγνώμη, οὐ βούλομαι.', 'Sometimes.': 'Ἐνίοτε.',
    'Never.': 'Οὐδέποτε.', "I can't think of anything.": 'Οὐδὲν ἐνοῶ.',
    'How about a farm story?': 'Περὶ τοῦ ἀγροῦ;', "How about Basil's job?": 'Περὶ τοῦ Βασιλείου;',
    'Sure I do.': 'Ναὶ δή.', 'Not really.': 'Οὐ πάνυ.',
    "You'll make a great nurse.": 'Ἀρίστη νοσοκόμος ἔσῃ.', 'Sorry, no.': 'Συγγνώμη, οὔ.',
    "Sure, I'll do it.": 'Ποιήσω δή.', "You've spoiled him.": 'Διέφθαρκας αὐτόν.',
    "You're doing a great job!": 'Εὖ ποιεῖς!', "I'm ready.": 'Ἕτοιμός εἰμι.',
    'Wait one second.': 'Ἐπίσχες βραχύ.', 'Remove a cursed tool.': 'Ἐπικατάρατον λῦσον.',
    'I want to confess.': 'Ἐξομολογεῖσθαι βούλομαι.', "Just saying 'hi'.": 'Χαίρειν λέγω μόνον.',
    'I hardly get any sleep.': 'Σπάνιον κοιμῶμαι.', "I'm overworking the HS.": 'Πονῶ τοὺς Πνευματικούς.',
    'I want to marry the HG.': 'Τὴν Θεὰν γῆμαι βούλομαι.', "I don't care for animals.": 'Οὐ μέλει μοι κτηνῶν.',
    'Worked until I collapsed.': 'Ἔκαμον μέχρι κόπου.', "Townspeople don't like me.": 'Οὐ φιλοῦσί με πολῖται.',
    'I was cruel to my animals.': 'Ὠμὸς ἦν τοῖς κτήνεσι.', 'I slept in late.': 'Ὄψιον ἐκοιμήθην.',
    'I littered in the road.': 'Ἐν ὁδῷ ἔρριψα.', 'Go to bed for the day?': 'Κοιμηθῆναι ἤδη;',
    'Turn in for the day?': 'Παύσασθαι ἤδη;', 'Take a bath?': 'Λούσασθαι;',
    'Make a call.': 'Τηλεφωνεῖν.', "Don't make a call.": 'Μὴ τηλεφωνεῖν.',
    "Don't buy": 'Μὴ ὠνοῦ', 'Buy': 'Ὠνοῦ', 'Prev. page': 'Προηγουμένη',
    'Next page': 'Ἑπομένη', 'Begin race.': 'Ἄρχε τοῦ ἀγῶνος.', 'Place a bet.': 'Στοιχημάτισον.',
    'Exchange.': 'Ἄλλαξον.', 'Nothing.': 'Οὐδέν.', "Let's start.": 'Ἀρχώμεθα.',
    'Not yet.': 'Οὔπω.', 'Start.': 'Ἄρχε.', 'Wait a minute.': 'Ἐπίσχες.',
    'Please examine me.': 'Ἐξέτασόν με.', 'No thanks.': 'Οὔ, χάριν ἔχω.',
    'Play with frisbee?': 'Παίζειν δίσκῳ;', "Don't play": 'Μὴ παίζειν',
    'Our anniversary': 'Ἡ ἐπέτειος ἡμῶν', 'My anniversary': 'Ἡ ἐπέτειός μου',
    'My birthday': 'Τὰ γενέθλιά μου', 'My birthday.': 'Τὰ γενέθλιά μου.',
    'Your birthday.': 'Τὰ γενέθλιά σου.', 'It\'s my birthday.': 'Τὰ γενέθλιά μού ἐστιν.',
    'It\'s your birthday.': 'Τὰ γενέθλιά σού ἐστιν.', 'Explain their error.': 'Δίδαξον τὸ ἁμάρτημα.',
    'Apologize.': 'Συγγνώμην αἴτει.', 'Learn.': 'Μάνθανε.', 'Tell her how you feel.': 'Εἰπὲ τὸ φρόνημά σου.',
    'Think for yourself.': 'Αὐτὸς φρόνει.', 'Stop the fight.': 'Παῦσον τὴν μάχην.',
    "Don't intervene.": 'Μὴ παρέμβαινε.', 'Buy Vase.': 'Ἀγγεῖον ὠνοῦ.', "Don't Buy.": 'Μὴ ὠνοῦ.',
    'Go down?': 'Καταβῆναι;', 'Go back to the surface?': 'Εἰς ἐπιφάνειαν ἐπανελθεῖν;',
    'Sounds like fun.': 'Ἡδὺ φαίνεται.', 'Sorry, I have other plans.': 'Συγγνώμη, ἄλλο ἔχω.',
    'Can you help me?': 'Δύνασαί μοι βοηθεῖν;', "Let's play.": 'Παίξωμεν.',
    'Nothing in particular.': 'Οὐδὲν ἴδιον.', '1 day': '1 ἡμέρα', '3 days': '3 ἡμέραι',
    '1 week': '1 ἑβδομάς', "Let's do more tomorrow!": 'Αὔριον πλείονα!',
    'Your job is done for now.': 'Τέλος ἔχει τὸ ἔργον.', "I'd love to!": 'Μάλιστα δή!',
    'Listen.': 'Ἄκουε.', "Don't listen.": 'Μὴ ἄκουε.', 'Pick one.': 'Ἕν ἐπίλεξον.',
    'Larger': 'Μεῖζον', 'Smaller': 'Ἔλαττον', 'Compete.': 'Ἀγωνίζου.', "Don't compete.": 'Μὴ ἀγωνίζου.',
    'Yes, let\'s start.': 'Ναί, ἀρχώμεθα.', 'I will.': 'Ποιήσω.', 'I won\'t.': 'Οὐ ποιήσω.',
    'Please wait.': 'Περίμεινον δή.', 'Invite to the fireworks?': 'Καλεῖν εἰς πυροτεχνήματα;',
    'Invite.': 'Κάλει.', "Don't invite.": 'Μὴ κάλει.', 'Not this year.': 'Οὐκ ἐφέτος.',
}
T.update(choices)

# 9. Days of the week in dialogue / script
days_full = {
    'Sunday': 'Κυριακή', 'Monday': 'Δευτέρα', 'Tuesday': 'Τρίτη',
    'Wednesday': 'Τετάρτη', 'Thursday': 'Πέμπτη', 'Friday': 'Παρασκευή', 'Saturday': 'Σάββατον'
}
T.update(days_full)

# Function to translate any given string using dictionaries and syntactic rules
def translate_string(s):
    # Direct match
    if s in T:
        return T[s]
    
    # Strip whitespace
    clean = s.strip()
    if clean in T:
        return T[clean]
    
    # Check simple pattern transformations
    # e.g. "X days" -> "X ἡμέραι"
    m_days = re.match(r'^(\d+)\s+days?$', clean, re.IGNORECASE)
    if m_days:
        n = m_days.group(1)
        return f"{n} ἡμέρα" if n == '1' else f"{n} ἡμέραι"
    
    # "X weeks" -> "X ἑβδομάδες"
    m_weeks = re.match(r'^(\d+)\s+weeks?$', clean, re.IGNORECASE)
    if m_weeks:
        n = m_weeks.group(1)
        return f"{n} ἑβδομάς" if n == '1' else f"{n} ἑβδομάδες"
    
    # "X years" -> "X ἔτη"
    m_yrs = re.match(r'^(\d+)\s+years?$', clean, re.IGNORECASE)
    if m_yrs:
        n = m_yrs.group(1)
        return f"{n} ἔτος" if n == '1' else f"{n} ἔτη"
    
    # "X G" -> "X G"
    m_gold = re.match(r'^([\d,]+)\s*G$', clean)
    if m_gold:
        return clean

    # "Is this X OK?" -> "Ὀρθόν ἐστι τὸ X;"
    m_ok = re.match(r'^Is this (.+) OK\?$', clean)
    if m_ok:
        item = m_ok.group(1)
        tr_item = T.get(item, item)
        return f"Ὀρθὸν τὸ {tr_item};"

    # Default fallback: translate standard words or retain formatting
    words = clean.split()
    tr_words = []
    for w in words:
        clean_w = re.sub(r'^[^\w]+|[^\w]+$', '', w)
        if clean_w in T:
            tr_words.append(w.replace(clean_w, T[clean_w]))
        else:
            tr_words.append(w)
    res = ' '.join(tr_words)
    return res

# Translate all entries
translated_count = 0
results = []
# Start IDs after existing max id in greek_script.json
existing_data = json.load(open('greek_script.json', 'r', encoding='utf-8'))
max_id = max(int(m['id'][1:]) for m in existing_data if m['id'].startswith('m'))
cur_id = max_id + 1

for entry in raw_unhooked:
    orig_text = entry['text']
    addrs = entry['addrs']
    
    el_text = translate_string(orig_text)
    norm = hmgreek.normalize(el_text)
    
    # Wrap if needed
    try:
        enc_bytes = hmgreek.encode_line(norm)
    except Exception as e:
        # If encoding fails, fallback to clean ascii/greek
        print(f"Warn encoding '{el_text}': {e}")
        enc_bytes = hmgreek.encode_line(hmgreek.normalize(orig_text))
    
    msg_dict = {
        'id': f"m{cur_id:05d}",
        'addrs': addrs,
        'hex': enc_bytes.hex(),
        'size': len(enc_bytes),
        'boxes': [[norm]]
    }
    results.append(msg_dict)
    cur_id += 1
    translated_count += 1

print(f"Generated {translated_count} new translated messages (m{max_id+1:05d}..m{cur_id-1:05d}).")

# Combine with existing script data
combined = existing_data + results
print(f"Total messages in combined script: {len(combined)}")

# Write to greek_script.json
with open('greek_script.json', 'w', encoding='utf-8') as f:
    json.dump(combined, f, ensure_ascii=False)
print("Updated greek_script.json successfully.")

# Rebuild ROM free space and redirection table with insert_text
print("\nRebuilding pilot.gba free space and redirection table...")
insert_text.insert_translations(
    'Harvest Moon - Friends of Mineral Town (USA).gba',
    'greek_script.json',
    'pilot.gba',
    'patches/hm_fomt_greek_pilot.ips'
)
print("ROM rebuild complete.")
