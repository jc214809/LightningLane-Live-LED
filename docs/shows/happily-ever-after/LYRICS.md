# Happily Ever After: the words, timed

What's sung and spoken in `sounds/happily-ever-after.wav`, with when each line starts, for timing the
score's scenes (`display/fireworks/shows/happily-ever-after.json`) to the music. Grouped under the
scene each line starts in, numbered as in [WATCH.md](WATCH.md).

- **How:** demucs (`htdemucs`) split the vocals from the music, then Whisper (`medium`, word timestamps)
  transcribed them (2026-10-15). A line's time is its first word's start, good to about ±0.3 s; a held
  note can stretch a word, so check a boundary by ear before trusting it to the tenth.
- **Clocks:** audio is the score's seconds; video is the recording's (video = audio × 1.001 + 10.19).
- **Gaps:** a scene with no lines is instrumental (or Whisper heard nothing): Part of Your World, the
  friendship medley's middle, Can You Feel the Love Tonight, the princess garden, the villains. Words
  are Whisper's: misheard ones are kept as heard ("Mr. Aladdin star"), not corrected from memory.

| Audio | Video | Line |
|---|---|---|
| **0** | **0:10.2** | **1.1 Theme fanfare** |
| 18.8 | 0:29.0 | And they all lived happily ever after. |
| **19** | **0:29.2** | **1.2 Narrator opening** |
| 23.0 | 0:33.2 | Each of us has a dream, a heart's desire. |
| 26.4 | 0:36.6 | It calls to us, and when we're brave enough to listen and bold enough to pursue, that |
| 33.7 | 0:44.0 | dream will lead us on a journey to discover who we're meant to be. |
| 39.5 | 0:49.7 | All we have to do is look inside our hearts and unlock the magic within. |
| **45.8** | **0:56.0** | **1.2a Magic from the keyhole** |
| **47** | **0:57.2** | **1.3 Happily Ever After theme song** |
| 47.1 | 0:57.4 | Ready to begin, let the wonder take hold Feel it draw you in, what's the moment unfold |
| 62.8 | 1:13.0 | Spark a dream that we're meant to follow Setting out for a new tomorrow |
| **63** | **1:13.3** | **1.4 Theme song builds** |
| 73.0 | 1:23.2 | Every step we take brings a new hope, a new day. |
| 81.3 | 1:31.5 | Every choice we make helps us find our own way. |
| 88.7 | 1:39.0 | Every wish finally put into motion, diving in with our hearts wide open. |
| 97.1 | 1:47.4 | The story comes alive |
| **98** | **1:48.3** | **2.1 Theme chorus** |
| 105.0 | 1:55.3 | When we look aside |
| 107.7 | 1:58.0 | A new adventure there in your eyes |
| 112.3 | 2:02.6 | There in your eyes |
| 114.7 | 2:05.0 | It's just beginning |
| 117.1 | 2:07.4 | Did your heart beat faster? |
| 120.9 | 2:11.2 | Each other and find your happily ever after |
| **128** | **2:18.3** | **2.2 Theme chorus (gold canopy)** |
| 128.4 | 2:18.7 | Find your happily ever after |
| **137** | **2:27.3** | **3.1 Wishing star lands on the castle** |
| 146.9 | 2:37.2 | The evening star is shining bright, so make a wish and hold on tight. |
| **147** | **2:37.3** | **3.2 Down in New Orleans (prologue)** |
| 158.9 | 2:49.3 | There's magic in the air tonight, and anything can happen. |
| **171** | **3:01.4** | **3.3 When You Wish Upon a Star (fanfare)** |
| **192** | **3:22.4** | **3.4 Part of Your World** |
| 213.7 | 3:44.1 | Out there, strolling by the sand, |
| **215** | **3:45.4** | **3.5 Out There** |
| 218.9 | 3:49.3 | Taste a morning out there, like ordinary men Who freely walk about there just one day |
| 231.6 | 4:02.0 | And then I swear I'll be content with my share |
| 241.4 | 4:11.8 | Won't resent, won't despair, old and bent, I won't care, I'll have spent one day out there. |
| **256** | **4:26.4** | **3.6 When You Wish Upon a Star (interlude)** |
| **268** | **4:38.5** | **3.7 Touch the Sky** |
| 268.5 | 4:39.0 | Your destiny lies within you, you just have to be brave enough to see it, and then your |
| 274.8 | 4:45.3 | journey begins. |
| 278.7 | 4:49.2 | I will hear their every story, take hold of my own dream, be as strong as the seas are |
| 287.2 | 4:57.7 | And proud as an eagle's scream, I will ride. |
| 292.7 | 5:03.2 | I will fly, chase the wind and touch the sky. |
| 297.0 | 5:07.5 | I will fly, chase the wind and touch the sky. |
| **303** | **5:13.5** | **4.1 Touch the Sky / Up** |
| 307.2 | 5:17.7 | Chase the wind, chase the wind and touch the sky. |
| **325** | **5:35.5** | **4.2 How Far I'll Go** |
| 335.6 | 5:46.1 | As I turn, I take, every trail I track, every path I make, every road leads back to the |
| 341.6 | 5:52.2 | I know where I cannot go, where I long to be |
| 348.9 | 5:59.4 | See the light as it shines on the sea, it's blinding |
| 354.2 | 6:04.8 | But no one knows how deep it goes |
| 360.0 | 6:10.5 | And it seems like it's calling out to me, so come find me |
| 365.0 | 6:15.5 | And let me know |
| 368.1 | 6:18.7 | What's beyond that line? Will I cross that line? |
| **370** | **6:20.6** | **4.3 How Far I'll Go (climax)** |
| 371.3 | 6:21.8 | The light you decided to see, it calls me |
| 376.0 | 6:26.5 | And no one knows, of where it goes |
| 381.9 | 6:32.5 | If the wind in my sail on the sea stays behind me |
| 386.9 | 6:37.4 | One day I'll know, how far I'll go |
| **398** | **6:48.6** | **5.1 Aladdin: a best friend by your side** |
| 403.7 | 6:54.3 | Trust me, having a best friend by your side opens up a whole new world of possibilities. |
| **412.5** | **7:03.1** | **5.2 Friend Like Me (instrumental)** |
| **428** | **7:18.6** | **5.3 Trashin' the Camp** |
| 429.5 | 7:20.1 | Zab-a da-zooba-doob, |
| 431.0 | 7:21.6 | Zab-a da-zooba-doob and D&E, |
| 434.2 | 7:24.8 | Zab-a da-zooba-doob, |
| 435.9 | 7:26.5 | Zab-a da-zooba-doob and D&E, |
| 439.3 | 7:29.9 | Zah bah dah, choo bah do, zah bah dah, do, dah, dah, dah, dah, dah, dah, dah, dah, |
| 445.0 | 7:35.7 | dee, dah, dee. |
| **446** | **7:36.6** | **5.4 Hakuna Matata** |
| **459.3** | **7:49.9** | **5.5 You've Got a Friend in Me** |
| **473.3** | **8:04.0** | **5.6 Friendship mash-up** |
| 503.6 | 8:34.3 | And when you're outside looking in, who's there to open the door? |
| **514** | **8:44.7** | **5.7 That's What Friends Are For** |
| 515.4 | 8:46.1 | That's what friends are for |
| **527** | **8:57.7** | **5.8 Friend Like Me (Genie)** |
| 529.6 | 9:00.3 | Mr. Aladdin star, have a wish, you're 203 |
| 537.4 | 9:08.2 | I'm on the job, you big gangbob, you ain't got |
| 541.6 | 9:12.3 | Never had a friend like me. |
| **554** | **9:24.7** | **5.9 Friend Like Me (finale)** |
| 554.2 | 9:25.0 | Never had a friend like me. |
| 562.1 | 9:32.8 | Ha! |
| **563** | **9:33.8** | **6.1 Olaf: some people are worth melting for** |
| 571.0 | 9:41.7 | Some people are worth melting for. |
| **576** | **9:46.8** | **6.2 Love Is an Open Door** |
| 578.2 | 9:48.9 | Say goodbye, say goodbye to the pain of the past |
| 584.0 | 9:54.7 | We don't have to feel it anymore |
| 590.8 | 10:01.6 | Love is an open door |
| 597.1 | 10:07.9 | Love is an open door |
| 603.1 | 10:13.9 | Love is an open door |
| **607** | **10:17.8** | **6.3 Can You Feel the Love Tonight** |
| 622.3 | 10:33.1 | You'll be in my heart no matter what they say, you'll be here in my heart always. |
| **623** | **10:33.8** | **6.4 You'll Be in My Heart** |
| **639** | **10:49.8** | **6.5 Princess garden** |
| 668.0 | 11:18.8 | And at last I see the light. |
| **668** | **11:18.9** | **6.6 I See the Light** |
| 673.0 | 11:23.9 | And it's like the fog is lifted. |
| 677.1 | 11:27.9 | And at last I see the light |
| 681.5 | 11:32.4 | And it's like the sky is new |
| 685.9 | 11:36.8 | And it's warm and real and bright |
| 690.6 | 11:41.5 | And the world is somehow shifted |
| **697** | **11:47.9** | **6.7 I See the Light (lanterns)** |
| 698.8 | 11:49.7 | All at once, everything is different |
| 704.3 | 11:55.2 | Now that I see you |
| **724** | **12:14.9** | **7.1 The Emperor's warning** |
| 728.0 | 12:18.9 | The flower that blooms in adversity is the most rare and beautiful of all. |
| **742** | **12:32.9** | **7.2 Villains attack** |
| **760** | **12:50.9** | **7.3 To Die For** |
| **777** | **13:08.0** | **7.4 He's a Pirate** |
| **806** | **13:37.0** | **7.5 He's a Pirate (green barrage)** |
| **812** | **13:43.0** | **7.6 He's a Pirate (red and gold)** |
| **837** | **14:08.0** | **7.7 He's a Pirate (finale)** |
| **849** | **14:20.0** | **8.1 Embers** |
| 861.9 | 14:32.9 | Look inside yourself. |
| 869.6 | 14:40.6 | You are more than what you have become. |
| **889** | **15:00.1** | **8.2 Go the Distance (the castle rebuilds)** |
| 889.2 | 15:00.3 | I have often dreamed of a far-off place Where a hero so welcome would be waiting for me |
| 902.5 | 15:13.6 | Where the crowds would cheer when they see my face |
| 908.1 | 15:19.2 | And a voice keeps saying this is where I'm meant to be |
| **915** | **15:26.1** | **8.3 Go the Distance** |
| 948.0 | 15:59.1 | I will beat the odds, I can go the distance, I will blaze the world, |
| 958.4 | 16:09.6 | Fearless, proud, and strong, I will please the gods. |
| 964.5 | 16:15.6 | I can go the distance till I find my hero's welcome rise. |
| 971.9 | 16:23.1 | Wherever I may be. |
| **976** | **16:27.2** | **8.4 Go the Distance (gold canopy)** |
| **992** | **16:43.2** | **9.1 Narrator closing** |
| 993.0 | 16:44.2 | And so our journey comes to an end, but yours continues on. |
| 1000.0 | 16:51.1 | Grab hold of your dreams and make them come true, for you are the key to unlocking your |
| 1006.5 | 16:57.7 | own magic. |
| 1008.3 | 16:59.5 | Now go, let your dreams guide you. |
| 1012.1 | 17:03.3 | Reach out and find your happily ever after. |
| 1016.7 | 17:07.9 | The battles, the stories, the losses in all the glory |
| **1017** | **17:08.2** | **10.1 Happily Ever After (reprise)** |
| 1025.0 | 17:16.2 | We're changed by the way we live every day |
| 1029.4 | 17:20.6 | Just look up and reach to the sky |
| 1033.4 | 17:24.6 | We all have the courage to fly |
| 1037.5 | 17:28.7 | You can fly |
| **1042.2** | **17:33.4** | **10.2 You Can Fly** |
| 1047.4 | 17:38.7 | The storm comes alive |
| 1054.5 | 17:45.7 | When we look inside |
| 1057.7 | 17:48.9 | The adventure |
| 1060.2 | 17:51.4 | There in your eyes |
| 1062.5 | 17:53.8 | Every new world is just beginning |
| 1068.0 | 17:59.3 | To know our feet faster |
| 1072.4 | 18:03.6 | We're gonna find our, we're gonna find our, we're gonna find our |
| **1080** | **18:11.3** | **10.3 You Can Fly (gold arcs)** |
| 1082.5 | 18:13.8 | Happily ever after |
| **1087** | **18:18.3** | **10.4 Final chorus, keyhole opens** |
| **1099.6** | **18:30.9** | **10.5 The last hit** |
