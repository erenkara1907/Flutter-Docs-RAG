# Hata analizi: başarısız sorular

## q002 (single, en) retrieval_miss + refused

- **Soru:** Is there a command to hide the red DEBUG ribbon while I'm debugging in VS Code?
- **Aranan sorgu:** debugShowCheckedModeBanner false
- **Beklenen sayfa(lar):** https://docs.flutter.dev/tools/vs-code
- **Beklenen sayfa derin aramada:** 6. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/tools/devtools/debugger
  2. https://docs.flutter.dev/platform-integration/web/web-content-in-flutter
  3. https://docs.flutter.dev/resources/faq
  4. https://docs.flutter.dev/testing/code-debugging
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q003 (single, en) retrieval_miss

- **Soru:** My app loses its state whenever the OS restarts it. Where do I learn how to restore it?
- **Aranan sorgu:** state restoration Flutter
- **Beklenen sayfa(lar):** https://docs.flutter.dev/data-and-backend/state-mgmt/intro
- **Beklenen sayfa derin aramada:** 8. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/platform-integration/android/restore-state-android
  2. https://docs.flutter.dev/platform-integration/ios/restore-state-ios
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/platform-integration/android/restore-state-android
- **Cevap:** To learn how to restore state when the OS restarts your app, see the "Restore state on Android > Overview" and the "Restore state on Android" sections. They explain enabling state restoration by setting a `restorationScopeId` on `MaterialApp`/`CupertinoApp`, assigning `restorationId` to widgets like `TextField` or `ScrollView`, and using `RestorableProperty` with `RestorationMixin` for custom widgets. They also cover using the restorable Navigator methods to preserve the navigation stack. Follow the steps outlined in those passages to implement short‑term state restoration.
- **Judge:** doğruluk=3 sadakat=5 | The reference answer directs the user to both the 'Restore state on Android' and 'Restore state on iOS' pages. The assistant's answer only directs the user to the 'Restore state on Android' sections, completely omitting the iOS page, which is a main point of the reference. Additionally, the assistant claims the Android pages explain how to restore state generally, whereas the provided passages indicate that the iOS page has specific setup requirements and refers back to the Android page for the core logic, making the assistant's omission of the iOS page a significant gap in guidance.

## q006 (single, en) refused

- **Soru:** In the SQLite to-do example, how does each new item get its id?
- **Aranan sorgu:** SQLite to-do example item id
- **Beklenen sayfa(lar):** https://docs.flutter.dev/app-architecture/design-patterns/sql
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/app-architecture/design-patterns/sql
  2. https://docs.flutter.dev/cookbook/persistence/sqlite
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q017 (single, en) low_accuracy

- **Soru:** What do I need to host so Android opens my app instead of the browser for a web link?
- **Aranan sorgu:** Android App Links intent filter
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/navigation/set-up-app-links
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/navigation/set-up-app-links
  2. https://docs.flutter.dev/flutter-for/android-devs
  3. https://docs.flutter.dev/ui/navigation/deep-linking
  4. https://docs.flutter.dev/deployment/android
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/cookbook/navigation/set-up-app-links
- **Cevap:** You must host a web domain that you control (e.g., on Firebase Hosting or GitHub Pages) and point the app‑link intent filter to that domain. The domain is referenced in the AndroidManifest.xml `<data android:scheme="http" android:host="example.com"/>` entry, and the hosted site will be used by Android to verify the link and open the app instead of the browser.
- **Judge:** doğruluk=1 sadakat=2 | The assistant's answer is factually incorrect regarding the specific requirement for Android to open the app instead of the browser. The reference answer correctly identifies that an `assetlinks.json` file containing the app's package name and signing key fingerprint is required for domain verification. The assistant claims that simply hosting a web domain and configuring the intent filter is sufficient, which is false; without the `assetlinks.json` file, Android will not verify the domain and will typically open the link in a browser or show a chooser, not exclusively in the app. Furthermore, the provided passages do not mention `assetlinks.json` or the verification process, so the assistant's claim that the hosted site is used for verification is unsupported by the text (and technically inaccurate based on the reference).

## q021 (single, en) refused

- **Soru:** How does a user type a line break in the AI chat prompt box on a phone versus a desktop?
- **Aranan sorgu:** line break AI chat prompt box phone desktop
- **Beklenen sayfa(lar):** https://docs.flutter.dev/ai/ai-toolkit/user-experience
- **Beklenen sayfa derin aramada:** 3. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/ai/ai-toolkit/chat-client-sample
  2. https://docs.flutter.dev/ai/ai-toolkit
  3. https://docs.flutter.dev/ai/ai-toolkit/user-experience
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q023 (single, en) low_accuracy

- **Soru:** My animations look janky. What should I check first when profiling?
- **Aranan sorgu:** Flutter animation jank profiling
- **Beklenen sayfa(lar):** https://docs.flutter.dev/perf/rendering-performance
- **Beklenen sayfa derin aramada:** 3. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/perf/ui-performance
  2. https://docs.flutter.dev/tools/devtools/performance
  3. https://docs.flutter.dev/perf/rendering-performance
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/perf/ui-performance, https://docs.flutter.dev/tools/devtools/performance
- **Cevap:** First open DevTools' Performance view and look at the frame rendering chart. A frame that takes longer than ~16 ms (the budget for 60 fps) is marked as janky, so check whether many frames exceed this threshold. If you see red‑highlighted slow frames, that indicates the source of the stutter and you can dig deeper into the cause.
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer focuses on using DevTools to identify janky frames (red overlay, >16ms), which is supported by the passages. However, it completely misses the main points of the reference answer: ensuring the app is built in profile mode (not debug) and checking for specific code issues like excessive UI rebuilds or non-lazy lists. Therefore, it fails to address the 'what to check first' aspect regarding build mode and common code causes.

## q026 (single, en) low_accuracy

- **Soru:** Which accessibility standards and regulations might apply to my Flutter app?
- **Aranan sorgu:** Flutter accessibility standards regulations
- **Beklenen sayfa(lar):** https://docs.flutter.dev/ui/accessibility
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/ui/accessibility
  2. https://docs.flutter.dev/resources/faq
  3. https://docs.flutter.dev/ui/accessibility/assistive-technologies
  4. https://docs.flutter.dev/ui/accessibility/web-accessibility
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/ui/accessibility
- **Cevap:** The UN Convention on the Rights of Persons with Disabilities (CRPD) is cited as a key international standard that calls for universal access to information systems, and many countries enforce accessibility requirements based on that convention or their own laws. Therefore, your Flutter app may need to comply with the CRPD and any national accessibility regulations that implement it.
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer focuses on the UN CRPD, which is mentioned in the passages, but it completely misses the specific technical standards (WCAG 2, EN 301 549) and documentation templates (VPAT) listed in the reference answer. While the claim about CRPD is supported by the text, the answer fails to address the core of the question regarding applicable standards as defined by the reference.

## q042 (multi, en) retrieval_miss

- **Soru:** How do I open a new screen with some data and get a value back when it closes?
- **Aranan sorgu:** Navigator.push with arguments get result
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/navigation/passing-data, https://docs.flutter.dev/cookbook/navigation/returning-data
- **Beklenen sayfa derin aramada:** 5. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/navigation/navigate-with-arguments
  2. https://docs.flutter.dev/learn/pathway/tutorial/navigation
  3. https://docs.flutter.dev/ui/navigation
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/cookbook/navigation/navigate-with-arguments, https://docs.flutter.dev/learn/pathway/tutorial/navigation, https://docs.flutter.dev/ui/navigation
- **Cevap:** Use `Navigator.of(context).push` (or `pushNamed` with the `arguments` property) to open the new screen, passing the data you need as shown in the snippets. In the called screen, when the user finishes, call `Navigator.of(context).pop(result)` where `result` is the value you want to return. The original screen can `await` the `push` call to receive that value when the route is popped. This pattern lets you both send data to the new screen and get a value back when it closes.
- **Judge:** doğruluk=5 sadakat=4 | The assistant's answer correctly describes the standard pattern for passing data and returning results using `Navigator.push` and `Navigator.pop`, which aligns perfectly with the reference answer. However, regarding faithfulness, the specific claim that one can `await` the `push` call to receive the result is not explicitly stated in the provided passages. While the passages show how to use `push` and `pop` (Passage 5) and how to pass arguments (Passage 1), they do not contain the code or text demonstrating the `Future` return value of `push` or the `await` mechanism for receiving the pop result. Therefore, this key part of the answer relies on external knowledge rather than the provided text.

## q045 (multi, en) retrieval_miss + refused

- **Soru:** How do I set up separate dev and production builds for both Android and iOS?
- **Aranan sorgu:** dev and production builds Android iOS Flutter
- **Beklenen sayfa(lar):** https://docs.flutter.dev/deployment/flavors, https://docs.flutter.dev/deployment/flavors-ios
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/flutter-for/android-devs
  2. https://docs.flutter.dev/resources/faq
  3. https://docs.flutter.dev/add-to-app/debugging
  4. https://docs.flutter.dev/platform-integration
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q052 (multi, en) refused

- **Soru:** How do I publish to Google Play and automate the release process?
- **Aranan sorgu:** publish to Google Play automate release process
- **Beklenen sayfa(lar):** https://docs.flutter.dev/deployment/android, https://docs.flutter.dev/deployment/cd
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/deployment/android
  2. https://docs.flutter.dev/deployment/linux
  3. https://docs.flutter.dev/deployment/windows
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q053 (multi, en) refused

- **Soru:** How do I validate a form and also read what the user entered?
- **Aranan sorgu:** validate form read user input FormField TextFormField
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/forms/validation, https://docs.flutter.dev/cookbook/forms/retrieve-input
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/forms/validation
  2. https://docs.flutter.dev/cookbook/forms/text-input
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -
