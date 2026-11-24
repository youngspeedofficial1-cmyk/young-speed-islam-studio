"""Writes videos_grave_story_en.json: 'The Night They Bury You' (2-3 min story, bilingual, Arabic rows)."""
import json, re

def strip(s): return re.sub(r'[ً-ْٰـ]', '', s)
B = json.load(open('/home/claude/hadith_data/bukhari.json'))['hadiths']
A = json.load(open('/home/claude/hadith_data/abudawud.json'))['hadiths']
def matn(hs, key): return re.sub(r'\s+', ' ', [h for h in hs if key in strip(h['arabic'])][0]['arabic']).strip()

R6514, R1338, R4753, R1369, R1377 = "Sahih al-Bukhari 6514", "Sahih al-Bukhari 1338", "Sunan Abi Dawud 4753", "Sahih al-Bukhari 1369", "Sahih al-Bukhari 1377"
S = "grave_story"

def L(text, text2, say, mood="soft", beat=None, hold=None, scene=S, **kw):
    d = dict(text=text, text2=text2, say=say, mood=mood, scene=scene)
    if beat: d["beat"] = beat
    if hold: d["hold"] = hold
    d.update(kw)
    return d

lines = [
 # ---- Act 1: the funeral
 L("One day, they will carry {you}.", "ایک دن، وہ {آپ} کو اٹھا کر لے جائیں گے۔", "One day, | they will carry you.", "heavy", "carry", 1.2, claim="interpretation", sfx="steps"),
 L("Your family. Your friends. Walking {slowly} behind you.", "آپ کے گھر والے، آپ کے دوست، {آہستہ آہستہ} آپ کے پیچھے چلتے ہوئے۔",
   "Your family. Your friends. | Walking slowly behind you.", "soft", None, 0.6, claim="interpretation", sfx="steps"),
 L("They will lower you into the {earth}…", "وہ آپ کو {زمین} میں اتار دیں گے…", "They will lower you | into the earth,", "heavy", "lower", 1.4, claim="interpretation", sfx="none"),
 L("and cover you with {soil}.", "اور آپ پر {مٹی} ڈال دیں گے۔", "and cover you with soil.", "heavy", "soil", 2.0, claim="interpretation", sfx="soil"),
 # ---- Act 2: three follow you
 L("The Prophet ﷺ said:", "نبی کریم ﷺ نے فرمایا:", "The Prophet, peace be upon him, said:", "neutral", sfx="none"),
 L("“When carried to his grave, a dead person is followed by {three},", "”جب میت کو قبر کی طرف لے جایا جاتا ہے تو {تین} چیزیں اس کے ساتھ جاتی ہیں،",
   "When carried to his grave, | a dead person is followed by three,", "soft", "three", 0.6, text0="يَتْبَعُ الْمَيِّتَ ثَلاَثَةٌ", text0_ref=R6514),
 L("his relative, his property, and his {deeds} follow him;", "اس کے گھر والے، اس کا مال، اور اس کے {اعمال}؛",
   "his relative, his property, | and his deeds follow him;", "soft", None, 0.6, text0="يَتْبَعُهُ أَهْلُهُ وَمَالُهُ وَعَمَلُهُ", text0_ref=R6514),
 L("relatives and his property go {back}", "گھر والے اور مال {واپس} لوٹ آتے ہیں", "relatives and his property | go back,", "soft", "back", 1.4, text0="فَيَرْجِعُ أَهْلُهُ وَمَالُهُ", text0_ref=R6514),
 L("while his deeds {remain} with him.”", "اور اس کے اعمال اس کے {ساتھ} رہ جاتے ہیں۔“", "while his deeds | *remain* with him.", "heavy", "remain", 2.0, text0="وَيَبْقَى عَمَلُهُ", text0_ref=R6514),
 # ---- Act 3: alone, the footsteps, the questions
 L("Then the last of them walks {away}.", "پھر آخری شخص بھی {چلا} جاتا ہے۔", "Then the last of them | walks away.", "soft", "steps", 1.6, claim="interpretation", sfx="steps"),
 L("The Prophet ﷺ said he even hears their {footsteps}.", "نبی ﷺ نے فرمایا: وہ ان کے {قدموں کی آہٹ} تک سنتا ہے۔",
   "The Prophet, peace be upon him, said | he even hears their footsteps.", "heavy", "hear", 1.0, text0="حَتَّى إِنَّهُ لَيَسْمَعُ قَرْعَ نِعَالِهِمْ", text0_ref=R1338, sfx="steps"),
 L("Then “two angels come to him and make him {sit}”.", "پھر ”دو فرشتے اس کے پاس آتے ہیں اور اسے {بٹھا} دیتے ہیں“۔",
   "Then two angels come to him, | and make him sit.", "firm", "angels", 1.4, text0="أَتَاهُ مَلَكَانِ فَأَقْعَدَاهُ", text0_ref=R1338, sfx="hit"),
 L("They ask him three questions.", "وہ اس سے تین سوال پوچھتے ہیں۔", "They ask him | three questions.", "neutral", sfx="none"),
 L("“Who is your {Lord}?”", "”تمہارا {رب} کون ہے؟“", "Who is your Lord?", "question", "q1", 1.0, text0="مَنْ رَبُّكَ", text0_ref=R4753, sfx="heart"),
 L("“What is your {religion}?”", "”تمہارا {دین} کیا ہے؟“", "What is your religion?", "question", "q2", 1.0, text0="مَا دِينُكَ", text0_ref=R4753, sfx="heart"),
 L("“Who is this {man} who was sent among you?”", "”یہ {شخص} کون ہے جو تم میں بھیجا گیا تھا؟“", "Who is this man, | who was sent among you?", "question", "q3", 1.4,
   text0="مَا هَذَا الرَّجُلُ الَّذِي بُعِثَ فِيكُمْ", text0_ref=R4753, sfx="heart"),
 # ---- Act 4: the believer
 L("The believer says: “My Lord is {Allah}.”", "مومن کہتا ہے: ”میرا رب {اللہ} ہے۔“", "The believer says: | My Lord is Allah.", "hope", "a1", 0.6, text0="رَبِّيَ اللَّهُ", text0_ref=R4753),
 L("“My religion is {Islam}.”", "”میرا دین {اسلام} ہے۔“", "My religion is Islam.", "hope", "a2", 0.6, text0="دِينِي الإِسْلاَمُ", text0_ref=R4753),
 L("“He is the {Messenger} of Allah ﷺ.”", "”وہ اللہ کے {رسول} ﷺ ہیں۔“", "He is the Messenger of Allah, | peace be upon him.", "hope", "a3", 1.0,
   text0="هُوَ رَسُولُ اللَّهِ صلى الله عليه وسلم", text0_ref=R4753),
 L("A crier calls from heaven: “My servant has spoken the {truth}”", "آسمان سے ایک پکارنے والا پکارتا ہے: ”میرے بندے نے {سچ} کہا“",
   "A crier calls from heaven: | My servant has spoken the truth.", "firm", "crier", 1.0, text0="أَنْ قَدْ صَدَقَ عَبْدِي", text0_ref=R4753, sfx="hit"),
 L("“so spread a bed for him from {Paradise}”, and a door to Paradise is opened for him.", "”اس کے لیے {جنت} کا بچھونا بچھا دو“، اور جنت کی طرف ایک دروازہ کھول دیا جاتا ہے۔",
   "so spread a bed for him from Paradise, | and a door to Paradise is opened for him.", "hope", "door", 1.0,
   text0="فَأَفْرِشُوهُ مِنَ الْجَنَّةِ، وَافْتَحُوا لَهُ بَابًا إِلَى الْجَنَّةِ", text0_ref=R4753),
 L("Its breeze and its {fragrance} reach him,", "اس کی ہوا اور {خوشبو} اس تک پہنچتی ہے،", "Its breeze, and its fragrance, | reach him,", "soft", "breeze", 0.8,
   text0="فَيَأْتِيهِ مِنْ رَوْحِهَا وَطِيبِهَا", text0_ref=R4753),
 L("and his grave is opened “as far as the eye can {see}.”", "اور اس کی قبر ”حدِ {نگاہ} تک“ کشادہ کر دی جاتی ہے۔", "and his grave is opened | as far as the eye can see.", "hope", "widen", 2.2,
   text0="وَيُفْتَحُ لَهُ فِيهَا مَدَّ بَصَرِهِ", text0_ref=R4753),
 L("He is shown his place in the Fire, then told: Allah gave you a place in {Paradise} instead.", "اسے جہنم میں اس کی جگہ دکھائی جاتی ہے، پھر کہا جاتا ہے: اللہ نے اس کے بدلے تمہیں {جنت} میں جگہ دی۔",
   "He is shown his place in the Fire, | then told: Allah gave you a place in Paradise instead.", "hope", "seats", 0.8,
   text0="انْظُرْ إِلَى مَقْعَدِكَ مِنَ النَّارِ أَبْدَلَكَ اللَّهُ بِهِ مَقْعَدًا مِنَ الْجَنَّةِ", text0_ref=R1338),
 L("“The dead person will see {both} his places.”", "”میت اپنی {دونوں} جگہیں دیکھے گی۔“", "The dead person | will see both his places.", "soft", "both", 2.0, text0="فَيَرَاهُمَا جَمِيعًا", text0_ref=R1338),
 # ---- Act 5: the one who did not believe
 L("But the one who did not {believe}…", "لیکن جس نے ایمان {نہیں} لایا…", "But the one | who did not believe,", "heavy", "other", 1.2, claim="interpretation", sfx="hit"),
 L("is asked the same three questions.", "اس سے بھی وہی تین سوال پوچھے جاتے ہیں۔", "is asked | the same three questions.", "heavy", sfx="heart"),
 L("“Alas, alas! I do not {know}.”", "”ہائے، ہائے! میں {نہیں} جانتا۔“", "Alas, alas! | I do not know.", "heavy", "dk", 1.2, text0="هَاهْ هَاهْ لاَ أَدْرِي", text0_ref=R4753),
 L("“I used to say what the {people} used to say!”", "”میں وہی کہتا تھا جو {لوگ} کہتے تھے!“", "I used to say | what the people used to say!", "heavy", None, 1.0, text0="كُنْتُ أَقُولُ مَا يَقُولُ النَّاسُ", text0_ref=R1338),
 L("A door to the {Fire} is opened for him, and its heat reaches him,", "اس کے لیے جہنم کا {دروازہ} کھول دیا جاتا ہے، اور اس کی تپش اس تک پہنچتی ہے،",
   "A door to the Fire is opened for him, | and its heat reaches him,", "heavy", "hell", 0.8, text0="وَافْتَحُوا لَهُ بَابًا إِلَى النَّارِ", text0_ref=R4753),
 L("and his grave is compressed “so that his ribs will be crushed {together}.”", "اور اس کی قبر اتنی تنگ کر دی جاتی ہے ”کہ اس کی {پسلیاں} ایک دوسرے میں گھس جاتی ہیں۔“",
   "and his grave is compressed, | so that his ribs will be crushed together.", "heavy", "narrow", 1.4,
   text0="وَيُضَيَّقُ عَلَيْهِ قَبْرُهُ حَتَّى تَخْتَلِفَ فِيهِ أَضْلاَعُهُ", text0_ref=R4753, sfx="hit"),
 L("He cries out, and everything near him hears it, except humans and {jinn}.", "وہ چیختا ہے، اور اس کے قریب ہر چیز سنتی ہے، سوائے انسانوں اور {جنوں} کے۔",
   "He cries out, and everything near him hears it, | except humans and jinn.", "heavy", "hammer", 1.4,
   text0="فَيَصِيحُ صَيْحَةً يَسْمَعُهَا مَنْ يَلِيهِ إِلاَّ الثَّقَلَيْنِ", text0_ref=R1338, sfx="hit"),
 # ---- Close: hope and action
 L("That night is coming for every one of {us}.", "یہ رات ہم میں سے {ہر ایک} پر آنی ہے۔", "That night is coming | for every one of us.", "heavy", "calm", 1.6, claim="interpretation"),
 dict(label="Allah says", text="يُثَبِّتُ اللَّهُ الَّذِينَ آمَنُوا بِالْقَوْلِ الثَّابِتِ فِي الْحَيَاةِ الدُّنْيَا وَفِي الْآخِرَةِ", font="arabic",
      sub="“Allah keeps firm those who believe, with the firm word, in worldly life and in the Hereafter.” (Ibrahim 14:27)",
      say="Allah keeps firm those who believe, with the firm word, | in worldly life, and in the Hereafter.", mood="hope", beat="ayah", hold=2.6, scene=S),
 L("This verse “was revealed concerning the punishment of the {grave}.”", "یہ آیت ”عذابِ {قبر} کے بارے میں نازل ہوئی۔“",
   "This verse was revealed | concerning the punishment of the grave.", "soft", None, 1.0, text0="نَزَلَتْ فِي عَذَابِ الْقَبْرِ", text0_ref=R1369, sub="(Sahih al-Bukhari 1369)", sfx="none"),
 L("The Prophet ﷺ used to make this dua:", "نبی کریم ﷺ یہ دعا کیا کرتے تھے:", "The Prophet, peace be upon him, | used to make this dua:", "soft", None, 0.4, scene="soft_light", sfx="none"),
 dict(text="اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنْ عَذَابِ الْقَبْرِ", font="arabic", sub="“O Allah, I seek refuge with You from the punishment of the grave” (Sahih al-Bukhari 1377)",
      say="O Allah, | I seek refuge with You from the punishment of the grave.", mood="soft", beat="dua", hold=2.6, scene="soft_light",
      arabic_source="hadith", hadith_ref=R1377, sfx="none"),
 L("Your three answers are being written {today}, by how you live. 🤍", "آپ کے تینوں جواب {آج} لکھے جا رہے ہیں، آپ کے جینے کے انداز سے۔",
   "Your three answers are being written today, | by how you live.", "firm", None, 1.0, scene="soft_light", claim="interpretation", sfx="none"),
 L("Say the dua tonight, and comment {Ameen}. 🤲", "آج رات یہ دعا پڑھیں، اور {آمین} لکھیں۔", "Say the dua tonight, | and comment Ameen.", "soft", "cta", 3.4, scene="soft_light", sfx="none"),
]

def src(ref, url, grade, wording, arabic=None):
    d = dict(ref=ref, url=url, grade=grade, wording=wording, checked="2026-11-22")
    if arabic: d.update(arabic=arabic, arabic_source="AhmedBaset/hadith-json")
    return d

v = dict(name="grave_story_en", lang="en", text2_lang="ur", style="animated_story", hook_type="bold_claim",
  topic="what happens after they bury you (story, 2-3 min)", title="The Night They Bury You",
  thumb_title="The Night They {Bury} You", thumb_title_ur="جس رات آپ کو دفن کیا جائے گا", thumb_t=95,
  caption="Your family turns back. Your wealth turns back. Only your deeds stay. 🤍 Watch till the end and say the dua tonight 🤲",
  hashtags=["#islamicreminder", "#hadith", "#grave", "#qabr", "#akhirah", "#muslim", "#deen"],
  sfx="dramatic",
  sources=[
   src(R6514, "https://sunnah.com/bukhari:6514", "sahih, agreed upon (Bukhari 6514, Muslim 2960)", "English per sunnah.com; narrated by Anas", matn(B, 'يتبع الميت ثلاثة')),
   src(R1338, "https://sunnah.com/bukhari:1338", "sahih, agreed upon (Bukhari 1338, Muslim 2870)", "English per sunnah.com; narrated by Anas; the hammer is mentioned only as 'he cries out'", matn(B, 'لا دريت ولا تليت')),
   src(R4753, "https://sunnah.com/abudawud:4753", "sahih (al-Albani); hasan (Zubair Ali Zai)", "English per sunnah.com and hadithunlocked.com; narrated by al-Bara' ibn 'Azib", matn(A, 'كأنما على رءوسنا الطير')),
   src(R1369, "https://sunnah.com/bukhari:1369", "sahih (Bukhari)", "'Allah will keep firm those who believe (14.27) was revealed concerning the punishment of the grave' (al-Bara')", matn(B, 'نزلت في عذاب القبر')),
   src(R1377, "https://sunnah.com/bukhari:1377", "sahih, agreed upon (Bukhari 1377, Muslim 588)", "English per HadeethEnc 3103; narrated by Abu Hurayrah", matn(B, 'اللهم إني أعوذ بك من عذاب القبر، ومن عذاب النار')),
  ], lines=lines)
json.dump(dict(videos=[v]), open('videos_grave_story_en.json', 'w'), ensure_ascii=False, indent=2)
print(len(lines), "lines")
