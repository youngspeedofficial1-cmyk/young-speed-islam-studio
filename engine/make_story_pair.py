"""Writes videos_cave_en.json and videos_last_man_en.json (2-3 min stories, bilingual, Arabic rows)."""
import json, re

def strip(s): return re.sub(r'[ً-ْٰـ]', '', s)
B = json.load(open('/home/claude/hadith_data/bukhari.json'))['hadiths']
M = json.load(open('/home/claude/hadith_data/muslim.json'))['hadiths']
def matn(hs, key): return re.sub(r'\s+', ' ', [h for h in hs if key in strip(h['arabic'])][0]['arabic']).strip()

def mk(S):
    def L(text, text2, say, mood="soft", beat=None, hold=None, scene=S, **kw):
        d = dict(text=text, text2=text2, say=say, mood=mood, scene=scene)
        if beat: d["beat"] = beat
        if hold: d["hold"] = hold
        d.update(kw)
        return d
    return L

# ============================================================ the cave
RC = "Sahih al-Bukhari 2272"
L = mk("cave_story")
cave = [
 L("Three men. One cave. And a rock that {sealed} it.", "تین آدمی۔ ایک غار۔ اور ایک پتھر جس نے اسے {بند} کر دیا۔", "Three men. One cave. | And a rock that sealed it.", "heavy", "walk", 1.0, claim="interpretation", sfx="steps"),
 L("The Prophet ﷺ told this story:", "نبی کریم ﷺ نے یہ واقعہ سنایا:", "The Prophet, peace be upon him, | told this story.", "neutral", sfx="none"),
 L("“Three men from among those who were before you, set out together till they reached a {cave} at night”", "”تم سے پہلے کے لوگوں میں سے تین آدمی چلے، یہاں تک کہ رات گزارنے کے لیے ایک {غار} میں پہنچے“",
   "Three men from among those who were before you, | set out together till they reached a cave at night.", "soft", "enter", 0.6,
   text0="انْطَلَقَ ثَلاَثَةُ رَهْطٍ مِمَّنْ كَانَ قَبْلَكُمْ حَتَّى أَوَوُا الْمَبِيتَ إِلَى غَارٍ", text0_ref=RC),
 L("“A big {rock} rolled down the mountain and closed the mouth of the cave.”", "”پہاڑ سے ایک بڑی {چٹان} لڑھکی اور غار کا منہ بند کر دیا۔“",
   "A big rock rolled down the mountain, | and closed the mouth of the cave.", "heavy", "rock", 1.2,
   text0="فَانْحَدَرَتْ صَخْرَةٌ مِنَ الْجَبَلِ فَسَدَّتْ عَلَيْهِمُ الْغَارَ", text0_ref=RC, sfx="hit"),
 L("{Darkness}. No way out.", "{اندھیرا}۔ نکلنے کا کوئی راستہ نہیں۔", "Darkness. | No way out.", "heavy", "dark", 1.4, claim="interpretation", sfx="heart"),
 L("“Nothing could save you from this rock but to invoke Allah by giving reference to the righteous {deed}”", "”اس چٹان سے صرف اپنے {نیک اعمال} کے واسطے کی دعا ہی بچا سکتی ہے“",
   "They said: Nothing could save you from this rock, | but to invoke Allah by giving reference to the righteous deed.", "firm", None, 0.8,
   text0="إِلاَّ أَنْ تَدْعُوا اللَّهَ بِصَالِحِ أَعْمَالِكُمْ", text0_ref=RC),
 # the first man
 L("The first said: “I had old {parents} and I never provided my family … with milk before them.”", "پہلے نے کہا: ”میرے بوڑھے {ماں باپ} تھے، اور میں ان سے پہلے اپنے گھر والوں کو دودھ نہیں دیتا تھا۔“",
   "The first said: I had old parents, | and I never provided my family with milk before them.", "soft", "pray1", 0.6,
   text0="كَانَ لِي أَبَوَانِ شَيْخَانِ كَبِيرَانِ وَكُنْتُ لاَ أَغْبِقُ قَبْلَهُمَا أَهْلاً وَلاَ مَالاً", text0_ref=RC),
 L("One night he came late, and found them {asleep}.", "ایک رات وہ دیر سے آیا، اور انہیں {سوتا} ہوا پایا۔", "One night he came late, | and found them asleep.", "soft", "mem1", 0.6,
   text0="فَوَجَدْتُهُمَا نَائِمَيْنِ", text0_ref=RC),
 L("“I kept on waiting for them to get up till the day {dawned}”", "”میں ان کے جاگنے کا انتظار کرتا رہا یہاں تک کہ {صبح} ہو گئی“", "I kept on waiting for them to get up, | till the day dawned.", "soft", None, 1.4,
   text0="فَلَبِثْتُ وَالْقَدَحُ عَلَى يَدَىَّ أَنْتَظِرُ اسْتِيقَاظَهُمَا حَتَّى بَرَقَ الْفَجْرُ", text0_ref=RC),
 L("“If I did that for Your Sake only, please relieve us from our critical {situation}”", "”اگر میں نے یہ صرف تیری رضا کے لیے کیا تھا، تو ہمیں اس {مصیبت} سے نکال دے“",
   "If I did that for Your Sake only, | please relieve us from our critical situation.", "hope", None, 0.6,
   text0="اللَّهُمَّ إِنْ كُنْتُ فَعَلْتُ ذَلِكَ ابْتِغَاءَ وَجْهِكَ فَفَرِّجْ عَنَّا", text0_ref=RC),
 L("“the rock shifted a {little} but they could not get out”", "”چٹان تھوڑی سی {سرکی}، مگر وہ نکل نہیں سکتے تھے“", "The rock shifted a little, | but they could not get out.", "firm", "shift1", 1.2,
   text0="فَانْفَرَجَتْ شَيْئًا لاَ يَسْتَطِيعُونَ الْخُرُوجَ", text0_ref=RC, sfx="hit"),
 # the second man
 L("The second loved his cousin more than anyone.", "دوسرا اپنی چچا زاد سے سب سے زیادہ محبت کرتا تھا۔", "The second loved his cousin | more than anyone.", "soft", "pray2", 0.4,
   text0="كَانَتْ لِي بِنْتُ عَمٍّ كَانَتْ أَحَبَّ النَّاسِ إِلَىَّ", text0_ref=RC),
 L("When he had the chance to {sin} with her, she said:", "جب اسے اس کے ساتھ {گناہ} کا موقع ملا، تو اس نے کہا:", "When he had the chance to sin with her, | she said:", "heavy", "mem2", 0.4),
 L("“It is illegal for you to outrage my chastity except by legitimate {marriage}.”", "”تمہارے لیے جائز نہیں کہ میری عزت کو {نکاح} کے بغیر پامال کرو۔“",
   "It is illegal for you to outrage my chastity, | except by legitimate marriage.", "firm", None, 0.8,
   text0="لاَ أُحِلُّ لَكَ أَنْ تَفُضَّ الْخَاتَمَ إِلاَّ بِحَقِّهِ", text0_ref=RC),
 L("He feared Allah, walked away, and left the {gold}.", "وہ اللہ سے ڈر گیا، چلا گیا، اور {سونا} بھی چھوڑ دیا۔", "He feared Allah, walked away, | and left the gold.", "firm", None, 1.0,
   text0="فَانْصَرَفْتُ عَنْهَا وَهْىَ أَحَبُّ النَّاسِ إِلَىَّ وَتَرَكْتُ الذَّهَبَ الَّذِي أَعْطَيْتُهَا", text0_ref=RC),
 L("“the rock shifted a little {more} but still they could not get out from there”", "”چٹان کچھ اور {سرکی}، مگر وہ پھر بھی نکل نہیں سکتے تھے“", "The rock shifted a little more, | but still they could not get out from there.", "firm", "shift2", 1.2,
   text0="فَانْفَرَجَتِ الصَّخْرَةُ غَيْرَ أَنَّهُمْ لاَ يَسْتَطِيعُونَ الْخُرُوجَ مِنْهَا", text0_ref=RC, sfx="hit"),
 # the third man
 L("The third had a worker who left without taking his {wage}.", "تیسرے کا ایک مزدور اپنی {مزدوری} لیے بغیر چلا گیا تھا۔", "The third had a worker, | who left without taking his wage.", "soft", "pray3", 0.4,
   text0="غَيْرَ رَجُلٍ وَاحِدٍ تَرَكَ الَّذِي لَهُ وَذَهَبَ", text0_ref=RC),
 L("“I invested his wages and I got much {property} thereby.”", "”میں نے اس کی مزدوری کو بڑھایا، یہاں تک کہ بہت {مال} ہو گیا۔“", "I invested his wages, | and I got much property thereby.", "hope", "mem3", 0.8,
   text0="فَثَمَّرْتُ أَجْرَهُ حَتَّى كَثُرَتْ مِنْهُ الأَمْوَالُ", text0_ref=RC),
 L("After some time, the worker came back for his {wage}.", "کچھ عرصے بعد مزدور اپنی {مزدوری} لینے آیا۔", "After some time, | the worker came back for his wage.", "soft", None, 0.4,
   text0="فَجَاءَنِي بَعْدَ حِينٍ فَقَالَ يَا عَبْدَ اللَّهِ أَدِّ إِلَىَّ أَجْرِي", text0_ref=RC),
 L("“All the camels, cows, sheep and slaves you see, are {yours}.”", "”یہ سب اونٹ، گائیں، بکریاں اور غلام جو تم دیکھ رہے ہو، {تمہارے} ہیں۔“", "All the camels, cows, sheep and slaves you see, | are yours.", "hope", None, 0.8,
   text0="كُلُّ مَا تَرَى مِنْ أَجْرِكَ مِنَ الإِبِلِ وَالْبَقَرِ وَالْغَنَمِ وَالرَّقِيقِ", text0_ref=RC),
 L("“Don't {mock} at me.”", "”میرا {مذاق} نہ اڑاؤ۔“", "Don't mock at me.", "question", None, 0.6, text0="لاَ تَسْتَهْزِئْ بِي", text0_ref=RC),
 L("He took it all, and left {nothing}.", "اس نے سب لے لیا، اور {کچھ} بھی نہ چھوڑا۔", "He took it all, | and left nothing.", "soft", None, 0.6,
   text0="فَأَخَذَهُ كُلَّهُ فَاسْتَاقَهُ فَلَمْ يَتْرُكْ مِنْهُ شَيْئًا", text0_ref=RC),
 L("“So, that rock shifted completely and they got out {walking}.”", "”پھر چٹان پوری ہٹ گئی اور وہ {چلتے ہوئے} باہر نکل آئے۔“", "So, that rock shifted completely, | and they got out walking.", "hope", "out", 2.4,
   text0="فَانْفَرَجَتِ الصَّخْرَةُ فَخَرَجُوا يَمْشُونَ", text0_ref=RC, sfx="hit"),
 L("Three hidden deeds. Done only for {Allah}.", "تین چھپے ہوئے عمل۔ صرف {اللہ} کے لیے۔", "Three hidden deeds. | Done only for Allah.", "firm", None, 0.8, claim="interpretation"),
 L("If a rock closed on you today, which deed would you {call} on?", "اگر آج آپ پر چٹان آ گرے، تو آپ کس عمل کا {واسطہ} دیں گے؟", "If a rock closed on you today, | which deed would you call on?", "question", None, 1.0, claim="interpretation"),
 dict(label="Allah says", text="وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا", font="arabic", sub="“And whoever fears Allah - He will make for him a way out” (At-Talaq 65:2)",
      say="And whoever fears Allah, | He will make for him a way out.", mood="hope", beat="ayah", hold=2.6, scene="cave_story"),
 L("Do one deed today that only {Allah} sees. 🤍", "آج ایک ایسا عمل کریں جو صرف {اللہ} دیکھے۔", "Do one deed today | that only Allah sees.", "firm", None, 1.0, scene="soft_light", claim="interpretation", sfx="none"),
 L("Comment {Ameen} if you will. 🤲", "اگر کریں گے تو {آمین} لکھیں۔", "Comment Ameen, | if you will.", "soft", "cta", 3.2, scene="soft_light", sfx="none"),
]

# ============================================================ the last man to enter Paradise
RM = "Sahih Muslim 187"
L = mk("last_man_story")
last = [
 L("The {last} man to enter Paradise…", "جنت میں داخل ہونے والا {آخری} آدمی…", "The last man | to enter Paradise.", "heavy", "walk", 0.8, claim="interpretation", sfx="steps"),
 L("The Prophet ﷺ said:", "نبی کریم ﷺ نے فرمایا:", "The Prophet, peace be upon him, said:", "neutral", sfx="steps"),
 L("“The last to enter Paradise would be a man who would walk once and {stumble} once”", "”جنت میں سب سے آخر میں داخل ہونے والا ایک آدمی ہوگا جو کبھی چلے گا اور کبھی {گرے} گا“",
   "The last to enter Paradise would be a man, | who would walk once, and stumble once,", "heavy", None, 0.4,
   text0="آخِرُ مَنْ يَدْخُلُ الْجَنَّةَ رَجُلٌ فَهُوَ يَمْشِي مَرَّةً وَيَكْبُو مَرَّةً", text0_ref=RM, sfx="steps"),
 L("“and be burnt by the Fire {once}.”", "”اور کبھی آگ اسے {جھلسائے} گی۔“", "and be burnt by the Fire once.", "heavy", None, 0.8, text0="وَتَسْفَعُهُ النَّارُ مَرَّةً", text0_ref=RM, sfx="heart"),
 L("“Then when he gets beyond it, he will turn to it and say: Blessed is He Who has saved me from {thee}.”", "”جب وہ اس سے آگے نکل جائے گا تو مڑ کر کہے گا: بابرکت ہے وہ ذات جس نے مجھے {تجھ} سے نجات دی۔“",
   "Then when he gets beyond it, he will turn to it and say: | Blessed is He, Who has saved me from thee.", "hope", "beyond", 0.6,
   text0="فَإِذَا مَا جَاوَزَهَا الْتَفَتَ إِلَيْهَا فَقَالَ تَبَارَكَ الَّذِي نَجَّانِي مِنْكِ", text0_ref=RM, sfx="hit"),
 L("“Allah has given me something He has not given to any one of those in earlier or later {times}.”", "”اللہ نے مجھے وہ دیا جو اگلوں پچھلوں میں سے {کسی} کو نہیں دیا۔“",
   "Allah has given me something | He has not given to any one of those in earlier or later times.", "hope", "turn", 0.6,
   text0="لَقَدْ أَعْطَانِيَ اللَّهُ شَيْئًا مَا أَعْطَاهُ أَحَدًا مِنَ الأَوَّلِينَ وَالآخِرِينَ", text0_ref=RM),
 L("“Then a {tree} would be raised up for him”", "”پھر اس کے لیے ایک {درخت} بلند کیا جائے گا“", "Then a tree | would be raised up for him.", "soft", "tree1", 1.2, text0="فَتُرْفَعُ لَهُ شَجَرَةٌ", text0_ref=RM, sfx="none"),
 L("He says: “bring me near this tree so that I may take shelter in its {shade} and drink of its water.”", "وہ کہے گا: ”مجھے اس درخت کے قریب کر دے تاکہ میں اس کے {سائے} میں رہوں اور اس کا پانی پیوں۔“",
   "He says: bring me near this tree, | so that I may take shelter in its shade, and drink of its water.", "soft", None, 0.4,
   text0="أَىْ رَبِّ أَدْنِنِي مِنْ هَذِهِ الشَّجَرَةِ فَلأَسْتَظِلَّ بِظِلِّهَا وَأَشْرَبَ مِنْ مَائِهَا", text0_ref=RM),
 L("Allah says: “O son of Adam, if I grant you this, you will ask Me for something {else}.”", "اللہ فرمائے گا: ”اے ابنِ آدم! اگر میں تجھے یہ دے دوں تو تو مجھ سے {کچھ اور} مانگے گا۔“",
   "Allah says: O son of Adam, | if I grant you this, you will ask Me for something else.", "firm", None, 0.4,
   text0="يَا ابْنَ آدَمَ لَعَلِّي إِنْ أَعْطَيْتُكَهَا سَأَلْتَنِي غَيْرَهَا", text0_ref=RM),
 L("He promises not to ask for anything {else}.", "وہ وعدہ کرتا ہے کہ {کچھ اور} نہیں مانگے گا۔", "He promises | not to ask for anything else.", "soft", None, 0.4, text0="وَيُعَاهِدُهُ أَنْ لاَ يَسْأَلَهُ غَيْرَهَا", text0_ref=RM),
 L("“His Lord would excuse him because He sees what he cannot help {desiring}; so He would bring him near it”", "”اس کا رب اسے معذور سمجھے گا کیونکہ وہ ایسی چیز دیکھ رہا ہے جس پر اسے {صبر} نہیں، پھر اسے اس کے قریب کر دے گا“",
   "His Lord would excuse him, because He sees what he cannot help desiring; | so He would bring him near it.", "hope", "near1", 1.2,
   text0="وَرَبُّهُ يَعْذِرُهُ لأَنَّهُ يَرَى مَا لاَ صَبْرَ لَهُ عَلَيْهِ فَيُدْنِيهِ مِنْهَا", text0_ref=RM),
 L("“Afterwards a tree more {beautiful} than the first would be raised up before him”", "”پھر اس کے سامنے پہلے سے زیادہ {خوبصورت} درخت بلند کیا جائے گا“",
   "Afterwards a tree more beautiful than the first, | would be raised up before him.", "hope", "tree2", 1.2,
   text0="ثُمَّ تُرْفَعُ لَهُ شَجَرَةٌ هِيَ أَحْسَنُ مِنَ الأُولَى", text0_ref=RM),
 L("He asks again. He promises {again}.", "وہ پھر مانگتا ہے۔ {پھر} وعدہ کرتا ہے۔", "He asks again. | He promises again.", "soft", None, 0.4, text0="لاَ أَسْأَلُكَ غَيْرَهَا", text0_ref=RM),
 L("And again, his Lord brings him {near}.", "اور پھر اس کا رب اسے {قریب} کر دیتا ہے۔", "And again, | his Lord brings him near.", "hope", "near2", 1.2,
   text0="فَيُدْنِيهِ مِنْهَا فَيَسْتَظِلُّ بِظِلِّهَا وَيَشْرَبُ مِنْ مَائِهَا", text0_ref=RM),
 L("“Then a tree would be raised up for him at the gate of the {Paradise}, more beautiful than the first two.”", "”پھر جنت کے {دروازے} پر اس کے لیے ایک درخت بلند کیا جائے گا، جو پہلے دونوں سے زیادہ خوبصورت ہوگا۔“",
   "Then a tree would be raised up for him at the gate of the Paradise, | more beautiful than the first two.", "hope", "tree3", 1.4,
   text0="ثُمَّ تُرْفَعُ لَهُ شَجَرَةٌ عِنْدَ بَابِ الْجَنَّةِ هِيَ أَحْسَنُ مِنَ الأُولَيَيْنِ", text0_ref=RM, sfx="hit"),
 L("“O son of Adam! did you not promise Me that you would not ask Me anything {else}?”", "”اے ابنِ آدم! کیا تو نے وعدہ نہیں کیا تھا کہ {کچھ اور} نہیں مانگے گا؟“",
   "O son of Adam! | Did you not promise Me that you would not ask Me anything else?", "question", None, 0.4,
   text0="يَا ابْنَ آدَمَ أَلَمْ تُعَاهِدْنِي أَنْ لاَ تَسْأَلَنِي غَيْرَهَا", text0_ref=RM),
 L("“Yes, my Lord, but I shall not ask Thee for anything {else}.”", "”کیوں نہیں، اے میرے رب! بس یہ، اس کے بعد {کچھ اور} نہیں مانگوں گا۔“",
   "Yes, my Lord, | but I shall not ask Thee for anything else.", "soft", None, 0.4, text0="بَلَى يَا رَبِّ هَذِهِ لاَ أَسْأَلُكَ غَيْرَهَا", text0_ref=RM),
 L("Near it, “he would hear the {voices} of the inhabitants of the Paradise.”", "اس کے قریب ”وہ جنت والوں کی {آوازیں} سنے گا۔“", "Near it, | he would hear the voices of the inhabitants of the Paradise.", "hope", "near3", 1.2,
   text0="فَيَسْمَعُ أَصْوَاتَ أَهْلِ الْجَنَّةِ", text0_ref=RM),
 L("“O my Lord! admit me to {it}.”", "”اے میرے رب! مجھے اس میں {داخل} کر دے۔“", "O my Lord! | Admit me to it.", "hope", "voices", 1.0, text0="أَىْ رَبِّ أَدْخِلْنِيهَا", text0_ref=RM),
 L("“O son of Adam, what will bring an end to your {requests} to Me?”", "”اے ابنِ آدم! تیری {خواہشیں} کہاں ختم ہوں گی؟“", "O son of Adam, | what will bring an end to your requests to Me?", "soft", "admit", 0.4,
   text0="يَا ابْنَ آدَمَ مَا يَصْرِينِي مِنْكَ", text0_ref=RM),
 L("“Will it please you if I give you the whole {world} and a like one along with it?”", "”کیا تو خوش ہوگا اگر میں تجھے پوری {دنیا} اور اس جیسی ایک اور دے دوں؟“",
   "Will it please you, | if I give you the whole world, and a like one along with it?", "hope", "world", 1.2,
   text0="أَيُرْضِيكَ أَنْ أُعْطِيَكَ الدُّنْيَا وَمِثْلَهَا مَعَهَا", text0_ref=RM, sfx="hit"),
 L("“O my Lord! art Thou mocking at me, though Thou art the Lord of the {worlds}?”", "”اے میرے رب! کیا تو مجھ سے مذاق کرتا ہے، حالانکہ تو {رب العالمین} ہے؟“",
   "O my Lord! | Art Thou mocking at me, though Thou art the Lord of the worlds?", "question", None, 0.6,
   text0="يَا رَبِّ أَتَسْتَهْزِئُ مِنِّي وَأَنْتَ رَبُّ الْعَالَمِينَ", text0_ref=RM),
 L("Ibn Mas'ud laughed, and said the Messenger of Allah ﷺ {laughed} the same way.", "ابن مسعود ہنسے، اور کہا کہ رسول اللہ ﷺ بھی اسی طرح {ہنسے} تھے۔",
   "Ibn Mas'ud laughed, | and said the Messenger of Allah, peace be upon him, laughed the same way.", "hope", "laugh", 0.4,
   text0="هَكَذَا ضَحِكَ رَسُولُ اللَّهِ صلى الله عليه وسلم", text0_ref=RM),
 L("He ﷺ said it was because of the laugh of the Lord of the worlds, Who will {say}:", "آپ ﷺ نے فرمایا: رب العالمین کے ہنسنے کی وجہ سے، جو {فرمائے} گا:",
   "He said it was because of the laugh of the Lord of the worlds, | Who will say:", "soft", None, 0.2, text0="مِنْ ضِحْكِ رَبِّ الْعَالَمِينَ", text0_ref=RM),
 L("“I am not mocking at you, but I have power to do whatever I {will}.”", "”میں تجھ سے مذاق نہیں کرتا، بلکہ میں جو چاہوں اس پر {قادر} ہوں۔“",
   "I am not mocking at you, | but I have power to do whatever I will.", "firm", "power", 2.0,
   text0="إِنِّي لاَ أَسْتَهْزِئُ مِنْكَ وَلَكِنِّي عَلَى مَا أَشَاءُ قَادِرٌ", text0_ref=RM, sfx="hit"),
 L("If this is the {last} one to enter… imagine the first.", "اگر یہ {آخری} داخل ہونے والا ہے… تو پہلے کا سوچیں۔", "If this is the last one to enter, | imagine the first.", "hope", None, 1.0, claim="interpretation"),
 dict(label="Allah says", text="فَمَن زُحْزِحَ عَنِ النَّارِ وَأُدْخِلَ الْجَنَّةَ فَقَدْ فَازَ", font="arabic",
      sub="“So he who is drawn away from the Fire and admitted to Paradise has attained [his desire].” (Al-Imran 3:185)",
      say="So he who is drawn away from the Fire, and admitted to Paradise, | has attained his desire.", mood="hope", beat="ayah", hold=3.0, scene="last_man_story"),
 L("Never stop asking {Allah}. 🤲", "اللہ سے {مانگنا} کبھی نہ چھوڑیں۔", "Never stop | asking Allah.", "firm", None, 1.0, scene="soft_light", claim="interpretation", sfx="none"),
 L("Comment {Ya Rabb} if you want Jannah. 🤍", "اگر جنت چاہیے تو {یا رب} لکھیں۔", "Comment Ya Rabb, | if you want Jannah.", "soft", "cta", 3.2, scene="soft_light", sfx="none"),
]

def src(ref, url, grade, wording, arabic):
    return dict(ref=ref, url=url, grade=grade, wording=wording, checked="2026-11-22", arabic=arabic, arabic_source="AhmedBaset/hadith-json")

V1 = dict(name="cave_story_en", lang="en", text2_lang="ur", style="animated_story", hook_type="bold_claim", topic="the three men in the cave (Bukhari 2272)",
  title="Three Men Trapped in a Cave", thumb_title="Three Men {Trapped} in a Cave", thumb_title_ur="غار میں پھنسے تین آدمی", thumb_t=40, sfx="dramatic",
  caption="A rock sealed the cave. Three hidden deeds opened it. 🤍 Which deed would you call on? 👇",
  hashtags=["#islamicreminder", "#hadith", "#islamicstory", "#ikhlas", "#dua", "#muslim", "#deen"],
  sources=[src(RC, "https://sunnah.com/bukhari:2272", "sahih, agreed upon (Bukhari 2272, Muslim 2743)", "English per sunnah.com; narrated by Abdullah ibn Umar; the second man's account is summarised modestly", matn(B, 'فانحدرت صخرة من الجبل'))],
  lines=cave)
V2 = dict(name="last_man_en", lang="en", text2_lang="ur", style="animated_story", hook_type="bold_claim", topic="the last man to enter Paradise (Muslim 187)",
  title="The Last Man to Enter Paradise", thumb_title="The {Last} Man to Enter Paradise", thumb_title_ur="جنت میں داخل ہونے والا آخری آدمی", thumb_t=128, sfx="dramatic",
  caption="He kept asking, and Allah kept giving. Imagine the first, if this is the last 🤍 Comment Ya Rabb 👇",
  hashtags=["#islamicreminder", "#hadith", "#jannah", "#islamicstory", "#allahsmercy", "#muslim", "#deen"],
  sources=[src(RM, "https://sunnah.com/muslim:187", "sahih (Muslim)", "English per sunnah.com; narrated by Ibn Mas'ud", matn(M, 'آخر من يدخل الجنة رجل'))],
  lines=last)
for f, v in (("videos_cave_en.json", V1), ("videos_last_man_en.json", V2)):
    json.dump(dict(videos=[v]), open(f, "w"), ensure_ascii=False, indent=2)
    print(f, len(v["lines"]), "lines")
