"""Writes videos_batch2_en.json. NOTE: the JSON was later edited in place (verify --fix, text0 Arabic rows, emojis) - do not re-run this or those edits are lost."""
import json

SAID = dict(text="The Prophet ﷺ said:", text2="نبی کریم ﷺ نے فرمایا:", say="The Prophet, peace be upon him, said:", mood="neutral")


def L(text, text2=None, say=None, mood="soft", beat=None, hold=None, interp=False, **kw):
    d = dict(text=text)
    if text2:
        d["text2"] = text2
    d["say"] = say or text.replace("{", "").replace("}", "").replace("“", "").replace("”", "")
    d["mood"] = mood
    if beat:
        d["beat"] = beat
    if hold:
        d["hold"] = hold
    if interp:
        d["claim"] = "interpretation"
    d.update(kw)
    return d


def card(ar, sub, say, ref, beat="card", hold=1.8):
    return dict(text=ar, font="arabic", sub=sub, say=say, mood="soft", beat=beat, hold=hold,
                arabic_source="hadith", hadith_ref=ref)


def ayah(ar, sub, say, beat="ayah", hold=3.0, label="Allah says", mood="soft"):
    d = dict(text=ar, font="arabic", sub=sub, say=say, mood=mood, beat=beat, hold=hold)
    if label:
        d["label"] = label
    return d


def src(ref, url, grade, wording):
    return dict(ref=ref, url=url, grade=grade, wording=wording, checked="2026-11-14")


V = []

# 1 ------------------------------------------------------------ anger
V.append(dict(name="anger_strong_en", scene="anger_calm", hook_type="question", topic="controlling anger",
    title="Who Is Really Strong?", caption="Real strength isn't in your fists, it's in the moment you hold back 🤍 Send this to someone who needs it 👇",
    hashtags=["#islamicreminder", "#hadith", "#anger", "#selfcontrol", "#sunnah", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 6114", "https://hadithunlocked.com/bukhari:6114", "sahih, agreed upon (Bukhari & Muslim)",
                 "English per hadithunlocked translation; narrated by Abu Hurayrah")],
    lines=[
        L("Think you're {strong}?", "سمجھتے ہیں آپ {طاقتور} ہیں؟", mood="question", beat="hook", hold=1.6, interp=True),
        dict(SAID),
        L("“The strong is not the one who {overcomes} the people by his strength,", "”طاقتور وہ نہیں جو لوگوں کو اپنی طاقت سے {پچھاڑ} دے،",
          say="The strong is not the one | who overcomes the people by his strength,", beat="wrestle", hold=1.0),
        L("but the strong is the one who {controls himself}", "بلکہ طاقتور وہ ہے جو {اپنے آپ پر قابو} رکھے",
          say="but the strong is the one who *controls himself*", mood="firm", beat="strong", hold=0.8),
        L("while in {anger}.”", "غصے کے {وقت}۔“", mood="soft", beat="calm", hold=2.6),
        card("إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ عِنْدَ الْغَضَبِ", "(Sahih al-Bukhari 6114)", "Reported by al-Bukhari and Muslim.", "Sahih al-Bukhari 6114"),
        L("Next time anger rises, {pause}. That pause is strength.", "اگلی بار غصہ آئے تو {رک جائیں}۔ یہی رکنا طاقت ہے۔",
          say="Next time anger rises, pause. | That pause is strength.", mood="firm", beat="reflect", interp=True),
        ayah("وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ وَاللَّهُ يُحِبُّ الْمُحْسِنِينَ",
             "“…who restrain anger and who pardon the people - and Allah loves the doers of good.” (Al-Imran 3:134)",
             "Who restrain anger, and who pardon the people, | and Allah loves the doers of good."),
        L("Who needs this reminder? {Send} it to them.", "یہ یاددہانی کس کو چاہیے؟ انہیں {بھیجیں}۔",
          say="Who needs this reminder? | Send it to them.", beat="cta", hold=3.2),
    ]))

# 2 ------------------------------------------------------------ charity
V.append(dict(name="charity_wealth_en", scene="charity_jar", hook_type="question", topic="charity does not decrease wealth",
    title="Charity Never Makes You Poorer", caption="Afraid giving will leave you with less? The Prophet ﷺ said the opposite 🤍 Give something small today and comment done 👇",
    hashtags=["#islamicreminder", "#hadith", "#sadaqah", "#charity", "#rizq", "#muslim", "#deen"],
    sources=[src("Sahih Muslim 2588", "https://hadithunlocked.com/muslim:2588", "sahih (Muslim)",
                 "English per hadithunlocked translation; narrated by Abu Hurayrah")],
    lines=[
        L("Afraid giving will make you {poorer}?", "ڈر ہے کہ دینے سے آپ {غریب} ہو جائیں گے؟", mood="question", beat="give", hold=1.6, interp=True),
        dict(SAID),
        L("“Charity does not {decrease} wealth,", "”صدقہ مال میں {کمی} نہیں کرتا،", mood="firm", beat="same", hold=1.2),
        L("no one forgives another except that Allah increases his {honor},", "جو کسی کو معاف کرے، اللہ اس کی {عزت} بڑھا دیتا ہے،",
          say="no one forgives another, | except that Allah increases his honor,", beat="forgive", hold=1.0),
        L("and no one humbles himself for the sake of Allah except that Allah {raises} his status.”",
          "اور جو اللہ کے لیے عاجزی کرے، اللہ اسے {بلند} کر دیتا ہے۔“",
          say="and no one humbles himself for the sake of Allah, | except that Allah *raises* his status.", mood="hope", beat="humble", hold=2.8),
        card("مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ", "(Sahih Muslim 2588)", "Reported by Muslim.", "Sahih Muslim 2588"),
        L("What you give for Allah is never {lost}.", "جو اللہ کے لیے دیا، وہ کبھی {ضائع} نہیں ہوتا۔", say="What you give for Allah | is never lost.",
          mood="hope", beat="reflect", interp=True),
        ayah("وَمَا أَنفَقْتُم مِّن شَيْءٍ فَهُوَ يُخْلِفُهُ وَهُوَ خَيْرُ الرَّازِقِينَ",
             "“But whatever thing you spend [in His cause] - He will compensate it; and He is the best of providers.” (Saba 34:39)",
             "Whatever thing you spend, | He will compensate it, and He is the best of providers."),
        L("Give something small today, then comment {done}.", "آج کچھ تھوڑا سا دیں، پھر {ہو گیا} لکھیں۔",
          say="Give something small today, | then comment, done.", beat="cta", hold=3.2),
    ]))

# 3 ------------------------------------------------------------ the believer's affair
V.append(dict(name="believer_affair_en", scene="believer_two", hook_type="bold_claim", topic="gratitude and patience: every affair is good",
    title="Every Situation Is Good for a Believer", caption="Good days: gratitude. Hard days: patience. Either way, it's good for you 🤍 Which one are you in today? 👇",
    hashtags=["#islamicreminder", "#hadith", "#sabr", "#shukr", "#patience", "#muslim", "#deen"],
    sources=[src("Sahih Muslim 2999", "https://hadithunlocked.com/muslim:2999", "sahih (Muslim)",
                 "English per hadithunlocked translation; narrated by Suhayb ar-Rumi")],
    lines=[
        L("For a believer, {every} situation can be good.", "مومن کے لیے {ہر} حال خیر بن سکتا ہے۔", mood="firm", beat="hook", hold=1.4, interp=True),
        dict(SAID),
        L("“How wondrous is the affair of a believer, for there is {good} in every affair of his.",
          "”مومن کا معاملہ بھی عجیب ہے، اس کے ہر معاملے میں {خیر} ہے۔",
          say="How wondrous is the affair of a believer, | for there is good in every affair of his."),
        L("If times of {ease} strike him,", "اگر اسے {خوشی} ملے،", beat="ease", mood="hope", hold=0.6),
        L("he is {grateful}, which is good for him.", "تو وہ {شکر} کرتا ہے، اور یہ اس کے لیے بہتر ہے۔", beat="grateful", hold=1.6),
        L("If times of {distress} strike him,", "اور اگر اسے {تکلیف} پہنچے،", beat="distress", mood="heavy", hold=0.6),
        L("he is {patient}, which is also good for him.”", "تو وہ {صبر} کرتا ہے، اور یہ بھی اس کے لیے بہتر ہے۔“", beat="patient", hold=2.0),
        card("إِنَّ أَمْرَهُ كُلَّهُ خَيْرٌ", "(Sahih Muslim 2999)", "Reported by Muslim.", "Sahih Muslim 2999", beat="both"),
        ayah("إِنَّ اللَّهَ مَعَ الصَّابِرِينَ", "“Indeed, Allah is with the patient.” (Al-Baqarah 2:153)", "Indeed, Allah is with the patient.", hold=2.6),
        L("Which one are you in today? Comment {ease} or {patience}.", "آج آپ کس حال میں ہیں؟ {آسانی} یا {صبر} لکھیں۔",
          say="Which one are you in today? | Comment ease, or patience.", beat="cta", hold=3.2),
    ]))

# 4 ------------------------------------------------------------ mother
V.append(dict(name="your_mother_en", scene="mother_rank", hook_type="question", topic="the right of the mother",
    title="Your Mother, Your Mother, Your Mother", caption="He asked who deserves his best treatment. The answer came three times 🤍 Write a dua for your mother below 👇",
    hashtags=["#islamicreminder", "#hadith", "#mother", "#parents", "#jannah", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 5971", "https://hadithunlocked.com/bukhari:5971", "sahih, agreed upon (Bukhari & Muslim)",
                 "English per hadithunlocked translation ('Who is next?'); narrated by Abu Hurayrah")],
    lines=[
        L("Who deserves your {best} treatment?", "آپ کے بہترین سلوک کا {سب سے زیادہ} حق دار کون ہے؟", mood="question", beat="hook", hold=1.4, interp=True),
        L("A man asked the Prophet ﷺ who most deserves his {best companionship}.", "ایک شخص نے نبی ﷺ سے پوچھا: میرے {حسنِ سلوک} کا سب سے زیادہ حق دار کون ہے؟",
          say="A man asked the Prophet, peace be upon him, | who most deserves his best companionship.", mood="neutral", beat="ask"),
        L("He said: “Your {mother}.”", "آپ ﷺ نے فرمایا: ”تمہاری {ماں}۔“", say="He said: | Your mother.", mood="firm", beat="m1", hold=1.0),
        L("“Who is next?” “Your {mother}.”", "”پھر کون؟“ ”تمہاری {ماں}۔“", say="Who is next? | Your mother.", mood="firm", beat="m2", hold=1.0),
        L("“Who is next?” “Your {mother}.”", "”پھر کون؟“ ”تمہاری {ماں}۔“", say="Who is next? | Your mother.", mood="heavy", beat="m3", hold=1.0),
        L("“Who is next?” “Your {father}.”", "”پھر کون؟“ ”تمہارا {باپ}۔“", say="Who is next? | Your father.", mood="soft", beat="father", hold=1.6),
        card("قَالَ أُمُّكَ قَالَ ثُمَّ مَنْ قَالَ أُمُّكَ", "(Sahih al-Bukhari 5971)", "Reported by al-Bukhari and Muslim.", "Sahih al-Bukhari 5971"),
        L("Three times, {mother}. Call her today.", "تین بار {ماں}۔ آج ہی انہیں فون کریں۔", say="Three times, mother. | Call her today.",
          mood="soft", beat="reflect", interp=True),
        ayah("حَمَلَتْهُ أُمُّهُ وَهْنًا عَلَىٰ وَهْنٍ", "“His mother carried him, [increasing her] in weakness upon weakness” (Luqman 31:14)",
             "His mother carried him, | in weakness upon weakness."),
        L("Write a dua for your {mother} in the comments.", "کمنٹس میں اپنی {ماں} کے لیے دعا لکھیں۔", beat="cta", hold=3.2),
    ]))

# 5 ------------------------------------------------------------ river
V.append(dict(name="river_prayers_en", scene="river_five", hook_type="question", topic="the five prayers wash away sins",
    title="A River at Your Door", caption="Five times a day, a river at your door that washes away sins 🤍 Which prayer is hardest for you? 👇",
    hashtags=["#islamicreminder", "#hadith", "#salah", "#namaz", "#prayer", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 528", "https://hadithunlocked.com/bukhari:528", "sahih, agreed upon (Bukhari & Muslim)",
                 "English per hadithunlocked translation; narrated by Abu Hurayrah")],
    lines=[
        L("Imagine a {river} at your door…", "سوچیں، آپ کے دروازے پر ایک {دریا} ہو…", say="Imagine a river | at your door.", mood="soft", beat="river", hold=1.4),
        dict(SAID, beat="dirt"),
        L("“If there was a river at the door of anyone of you and he took a bath in it {five times} a day,",
          "”اگر تم میں سے کسی کے دروازے پر دریا ہو اور وہ اس میں دن میں {پانچ بار} نہائے،",
          say="If there was a river at the door of anyone of you, | and he took a bath in it five times a day,", beat="five"),
        L("would you notice any {dirt} on him?”", "تو کیا اس پر کوئی {میل} باقی رہے گا؟“", mood="question", hold=0.8),
        L("They said: “Not a trace of dirt would be {left}.”", "صحابہ نے کہا: ”ذرا سا میل بھی {باقی} نہیں رہے گا۔“",
          say="They said: | Not a trace of dirt would be left.", beat="clean", hold=1.0),
        L("“That is the example of the {five prayers} with which Allah blots out evil deeds.”",
          "”یہی مثال {پانچ نمازوں} کی ہے، جن سے اللہ گناہ مٹا دیتا ہے۔“",
          say="That is the example of the *five prayers*, | with which Allah blots out evil deeds.", mood="hope", beat="prayers", hold=2.2),
        card("فَذَلِكَ مِثْلُ الصَّلَوَاتِ الْخَمْسِ يَمْحُو اللَّهُ بِهَا الْخَطَايَا", "(Sahih al-Bukhari 528)", "Reported by al-Bukhari and Muslim.", "Sahih al-Bukhari 528"),
        ayah("إِنَّ الْحَسَنَاتِ يُذْهِبْنَ السَّيِّئَاتِ", "“Indeed, good deeds do away with misdeeds.” (Hud 11:114)", "Indeed, good deeds | do away with misdeeds.", hold=2.6),
        L("Which prayer is hardest for you? {Comment} it.", "آپ کے لیے کون سی نماز سب سے مشکل ہے؟ {کمنٹ} کریں۔",
          say="Which prayer is hardest for you? | Comment it.", mood="question", beat="cta", hold=3.2),
    ]))

# 6 ------------------------------------------------------------ speak good
V.append(dict(name="speak_good_en", scene="words_record", hook_type="bold_claim", topic="speak good or stay silent",
    title="Speak Good or Stay Silent", caption="Every word you say is written down. Speak good, or stay silent 🤍 Comment good if you'll try today 👇",
    hashtags=["#islamicreminder", "#hadith", "#tongue", "#akhlaq", "#manners", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 6018", "https://sunnah.com/bukhari:6018", "sahih (Bukhari); also Muslim 47",
                 "English per sunnah.com translation; narrated by Abu Hurayrah; only the third sentence of the hadith is quoted")],
    lines=[
        L("Every word you say is {written}.", "آپ کا ہر لفظ {لکھا} جاتا ہے۔", mood="firm", beat="hook", hold=1.4, interp=True),
        dict(SAID),
        L("“Anybody who believes in Allah and the {Last Day}", "”جو اللہ اور {آخرت} کے دن پر ایمان رکھتا ہے", say="Anybody who believes in Allah | and the Last Day,", hold=0.6),
        L("should talk what is {good}", "وہ {اچھی} بات کہے", say="should talk what is *good*,", mood="hope", beat="good", hold=1.6),
        L("or keep {quiet}.”", "یا {خاموش} رہے۔“", mood="firm", beat="silent", hold=2.2),
        card("فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ", "(Sahih al-Bukhari 6018)", "Reported by al-Bukhari and Muslim.", "Sahih al-Bukhari 6018"),
        L("Because every word is {recorded}.", "کیونکہ ہر لفظ {محفوظ} ہو رہا ہے۔", mood="heavy", beat="record", hold=1.0, interp=True),
        ayah("مَّا يَلْفِظُ مِن قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ", "“…utters no word except that with him is an observer prepared [to record].” (Qaf 50:18)",
             "He utters no word, | except that with him is an observer prepared to record.", mood="heavy"),
        L("Before you speak, ask: is it {good}? Comment {good} if you'll try.", "بولنے سے پہلے سوچیں: کیا یہ {اچھا} ہے؟ کوشش کریں گے تو {اچھا} لکھیں۔",
          say="Before you speak, ask: is it good? | Comment good, if you'll try.", beat="cta", hold=3.2, interp=True),
    ]))

# 7 ------------------------------------------------------------ traveler
V.append(dict(name="traveler_en", scene="traveler_road", hook_type="bold_claim", topic="be in this world like a traveler",
    title="Just Passing Through", caption="This world is a road, not a home. Travel light 🤍 Save this for the days you forget 👇",
    hashtags=["#islamicreminder", "#hadith", "#dunya", "#akhirah", "#traveler", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 6416", "https://hadithunlocked.com/bukhari:6416", "sahih (Bukhari)",
                 "English per hadithunlocked translation; narrated by Ibn Umar, including Ibn Umar's own statement after it")],
    lines=[
        L("This world is not your {home}.", "یہ دنیا آپ کا {گھر} نہیں۔", mood="firm", beat="hook", hold=1.4, interp=True),
        L("The Prophet ﷺ took Ibn Umar by the shoulder and said:", "نبی ﷺ نے ابن عمر رضی اللہ عنہ کا کندھا پکڑ کر فرمایا:",
          say="The Prophet, peace be upon him, | took Ibn Umar by the shoulder and said:", mood="neutral"),
        L("“Be in this world as though you were a {stranger}", "”دنیا میں ایسے رہو جیسے تم ایک {اجنبی} ہو", beat="stranger", hold=0.6),
        L("or a {traveler} passing through.”", "یا ایک {راہ گزر} مسافر۔“", say="or a *traveler* passing through.", beat="traveler", hold=1.6),
        card("كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ", "(Sahih al-Bukhari 6416)", "Reported by al-Bukhari.", "Sahih al-Bukhari 6416"),
        L("Ibn Umar used to say: “When you reach {evening}, do not wait for morning;", "ابن عمر کہا کرتے تھے: ”جب {شام} ہو تو صبح کا انتظار نہ کرو،",
          say="Ibn Umar used to say: | When you reach evening, do not wait for morning;", beat="evening"),
        L("when you reach {morning}, do not wait for evening.”", "اور جب {صبح} ہو تو شام کا انتظار نہ کرو۔“", say="when you reach morning, | do not wait for evening.", beat="morning"),
        L("Travel {light}. You're only passing through.", "{ہلکا} سفر کریں۔ آپ بس گزر رہے ہیں۔", say="Travel light. | You're only passing through.", beat="reflect", interp=True),
        ayah("وَمَا الْحَيَاةُ الدُّنْيَا إِلَّا مَتَاعُ الْغُرُورِ", "“And what is the worldly life except the enjoyment of delusion.” (Al-Hadid 57:20)",
             "And what is the worldly life, | except the enjoyment of delusion.", mood="heavy"),
        L("Save this for the days you {forget}.", "یہ ان دنوں کے لیے محفوظ کر لیں جب آپ {بھول} جائیں۔", say="Save this | for the days you forget.", beat="cta", hold=3.2),
    ]))

# 8 ------------------------------------------------------------ dua of Yunus
V.append(dict(name="yunus_dua_en", scene="three_darks", hook_type="bold_claim", topic="the dua of Yunus from the darknesses",
    title="A Dua From Three Darknesses", caption="He called out from the darkness of the night, the sea and the fish, and Allah answered 🤍 Say it in your hardest moment. Comment Ameen 👇",
    hashtags=["#islamicreminder", "#quran", "#dua", "#prophetyunus", "#hope", "#muslim", "#deen"],
    sources=[src("Tafsir Ibn Kathir on 21:87", "https://www.alim.org/quran/tafsir/ibn-kathir/surah/21/87/", "tafsir",
                 "'darknesses' = the darkness of the belly of the fish, the sea and the night (Ibn Mas'ud, similar from Ibn Abbas and others)")],
    lines=[
        L("Trapped in {three} darknesses…", "تین {اندھیروں} میں…", mood="heavy", beat="hook", hold=1.2, interp=True),
        L("the darkness of the {night},", "رات کا {اندھیرا}،", beat="night", hold=0.8, interp=True),
        L("the darkness of the {sea},", "سمندر کا {اندھیرا}،", beat="sea", hold=0.8, interp=True),
        L("and the darkness inside the {fish}.", "اور مچھلی کے پیٹ کا {اندھیرا}۔", beat="fish", hold=1.2, interp=True,
          sub="(Ibn Kathir, from Ibn Mas'ud)"),
        L("Prophet Yunus called out:", "حضرت یونس علیہ السلام نے پکارا:", say="Prophet Yunus, peace be upon him, | called out:", mood="neutral", beat="dua"),
        ayah("لَّا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ",
             "“There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.” (Al-Anbya 21:87)",
             "There is no deity except You; exalted are You. | Indeed, I have been of the wrongdoers.", beat="duacard", hold=2.4, label=None),
        ayah("فَاسْتَجَبْنَا لَهُ وَنَجَّيْنَاهُ مِنَ الْغَمِّ وَكَذَٰلِكَ نُنجِي الْمُؤْمِنِينَ",
             "“So We responded to him and saved him from the distress. And thus do We save the believers.” (Al-Anbya 21:88)",
             "So We responded to him, and saved him from the distress. | And thus do We save the believers.", beat="answered", hold=3.0, mood="hope"),
        L("If He answered from {there}, He can answer you {here}.", "اگر اُس نے {وہاں} سے سن لیا، تو آپ کی {یہاں} بھی سنے گا۔",
          say="If He answered from there, | He can answer you here.", mood="hope", beat="reflect", interp=True),
        L("Say it in your hardest moment. Comment {Ameen}.", "مشکل ترین لمحے میں یہ پڑھیں۔ {آمین} لکھیں۔", say="Say it in your hardest moment. | Comment, Ameen.", beat="cta", hold=3.2),
    ]))

# 9 ------------------------------------------------------------ hardship and ease (Quran, existing scenes)
V.append(dict(name="with_hardship_ease_en", scene=None, hook_type="question", topic="with hardship comes ease (94:5-6)",
    title="With Hardship Comes Ease", caption="Allah didn't say ease comes after hardship. He said it comes with it, and He said it twice 🤍 Comment Ameen if you need this today 👇",
    hashtags=["#islamicreminder", "#quran", "#hardship", "#sabr", "#hope", "#muslim", "#deen"],
    sources=[],
    lines=[
        L("Going through something {hard}?", "کسی {مشکل} سے گزر رہے ہیں؟", mood="question", beat="hook", hold=1.2, interp=True, scene="storm_clear"),
        L("Allah didn't only say ease comes {after} hardship.", "اللہ نے صرف یہ نہیں فرمایا کہ آسانی مشکل کے {بعد} آتی ہے۔",
          say="Allah didn't only say | ease comes after hardship.", mood="soft", interp=True, scene="storm_clear"),
        L("He said it comes {with} it.", "فرمایا: مشکل کے {ساتھ} آسانی ہے۔", say="He said it comes *with* it.", mood="firm", interp=True, scene="storm_clear"),
        dict(ayah("فَإِنَّ مَعَ الْعُسْرِ يُسْرًا", "“For indeed, with hardship [will be] ease.” (Ash-Sharh 94:5)", "For indeed, | with hardship will be ease.", hold=2.0), scene="desert_rain"),
        dict(ayah("إِنَّ مَعَ الْعُسْرِ يُسْرًا", "“Indeed, with hardship [will be] ease.” (Ash-Sharh 94:6)", "Indeed, | with hardship will be ease.", hold=2.0, label=None, mood="hope"), scene="desert_rain"),
        L("He said it {twice}.", "اور یہ بات {دو بار} فرمائی۔", mood="firm", interp=True, scene="desert_rain", hold=1.0),
        L("Your hardship is not {alone}. Ease is already with it.", "آپ کی مشکل {اکیلی} نہیں، آسانی اس کے ساتھ ہے۔",
          say="Your hardship is not alone. | Ease is already with it.", mood="hope", interp=True, scene="sunset"),
        L("Hold on. Make dua. {Keep going}.", "ثابت قدم رہیں۔ دعا کریں۔ {چلتے رہیں}۔", say="Hold on. Make dua. | Keep going.", mood="firm", interp=True, scene="sunset"),
        L("Comment {Ameen} if you need this today.", "اگر آج آپ کو اس کی ضرورت ہے تو {آمین} لکھیں۔", say="Comment Ameen, | if you need this today.", beat="cta", hold=3.2, scene="sunset"),
    ]))

# 10 ----------------------------------------------------------- hadith qudsi: walking / running
V.append(dict(name="nearer_running_en", scene="nearer_path", hook_type="bold_claim", topic="hadith qudsi: if he comes walking, I go running",
    title="Take One Step Toward Allah", caption="Take a step toward Allah. His answer is always more 🤍 Take your step today and comment Ya Allah 👇",
    hashtags=["#islamicreminder", "#hadith", "#hadithqudsi", "#dhikr", "#allahsmercy", "#muslim", "#deen"],
    sources=[src("Sahih al-Bukhari 7405", "https://hadithunlocked.com/bukhari:7405", "sahih, agreed upon (Bukhari & Muslim); hadith qudsi",
                 "English per hadithunlocked translation; narrated by Abu Hurayrah; the middle part (remembering in a gathering) is omitted")],
    lines=[
        L("Take one step toward {Allah}…", "اللہ کی طرف ایک {قدم} بڑھائیں…", say="Take one step | toward Allah.", mood="soft", beat="hook", hold=1.2, interp=True),
        L("The Prophet ﷺ said that Allah says:", "نبی ﷺ نے فرمایا کہ اللہ تعالیٰ فرماتا ہے:", say="The Prophet, peace be upon him, said that Allah says:", mood="neutral"),
        L("“I am as My servant {expects} Me to be,", "”میں اپنے بندے کے گمان کے {مطابق} ہوں،", beat="expect", hold=0.6),
        L("and I am with him if he {remembers} Me.", "اور جب وہ مجھے {یاد} کرتا ہے تو میں اس کے ساتھ ہوتا ہوں۔", beat="remember", hold=1.0),
        L("If he comes one {span} nearer to Me, I go one cubit nearer to him.", "اگر وہ ایک {بالشت} میرے قریب آئے، تو میں ایک ہاتھ اس کے قریب جاتا ہوں۔",
          say="If he comes one span nearer to Me, | I go one cubit nearer to him.", beat="span"),
        L("If he comes one {cubit} nearer to Me, I go two outstretched arms nearer to him.", "اگر وہ ایک ہاتھ قریب آئے، تو میں {دو بازوؤں} کے برابر قریب جاتا ہوں۔",
          say="If he comes one cubit nearer to Me, | I go two outstretched arms nearer to him.", beat="cubit"),
        L("And if he comes to Me walking, I go to him {running}.”", "اور اگر وہ میرے پاس چل کر آئے، تو میں اس کے پاس {دوڑ کر} جاتا ہوں۔“",
          say="And if he comes to Me walking, | I go to him *running*.", mood="hope", beat="walk", hold=2.6),
        card("وَإِنْ أَتَانِي يَمْشِي أَتَيْتُهُ هَرْوَلَةً", "(Sahih al-Bukhari 7405, hadith qudsi)", "Reported by al-Bukhari and Muslim.", "Sahih al-Bukhari 7405"),
        ayah("فَاذْكُرُونِي أَذْكُرْكُمْ", "“So remember Me; I will remember you.” (Al-Baqarah 2:152)", "So remember Me; | I will remember you.", hold=2.6),
        L("Take your step today. Comment {Ya Allah}.", "آج اپنا قدم بڑھائیں۔ {یا اللہ} لکھیں۔", say="Take your step today. | Comment, Ya Allah.", beat="cta", hold=3.2),
    ]))

out = []
for v in V:
    sc = v.pop("scene")
    for ln in v["lines"]:
        if sc and "scene" not in ln:
            ln["scene"] = sc
    v.update(lang="en", text2_lang="ur", style="explainer" if sc else "quran_focused", title_en=v["title"])
    out.append(v)
json.dump(dict(videos=out), open("videos_batch2_en.json", "w"), ensure_ascii=False, indent=2)
print(len(out), "videos")
