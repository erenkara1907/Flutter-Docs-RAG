# Hata analizi: başarısız sorular

## q002 (single, en) retrieval_miss + refused

- **Soru:** Is there a command to hide the red DEBUG ribbon while I'm debugging in VS Code?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/tools/vs-code
- **Beklenen sayfa derin aramada:** 5. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/tools/devtools/debugger
  2. https://docs.flutter.dev/testing/native-debugging
  3. https://docs.flutter.dev/tools/devtools/vscode
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q007 (single, en) retrieval_miss + refused

- **Soru:** How do I run staging and production variants of my app on Windows desktop?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/deployment/flavors-windows
- **Beklenen sayfa derin aramada:** 4. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/deployment/flavors-ios
  2. https://docs.flutter.dev/platform-integration/windows/building
  3. https://docs.flutter.dev/deployment/flavors
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q015 (single, en) refused

- **Soru:** Which command produces an App Store-ready bundle for my iOS app, and where does the output go?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/deployment/ios
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/deployment/ios
  2. https://docs.flutter.dev/deployment/macos
  3. https://docs.flutter.dev/deployment/flavors-ios
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q016 (single, en) retrieval_miss + low_accuracy

- **Soru:** Which system packages do I need on Ubuntu before installing Flutter?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/install/manual
- **Beklenen sayfa derin aramada:** 10. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/platform-integration/linux/building
  2. https://docs.flutter.dev/platform-integration/linux/setup
  3. https://docs.flutter.dev/learn/pathway/tutorial/set-up-state-project
  4. https://docs.flutter.dev/packages-and-plugins/using-packages
  5. https://docs.flutter.dev/platform-integration/android/setup
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/platform-integration/linux/setup
- **Cevap:** On Ubuntu you should install the development packages clang, cmake, ninja-build, pkg-config, libgtk-3-dev and libstdc++-12-dev before using Flutter. You can do this with the following command:
```console
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y clang cmake ninja-build pkg-config libgtk-3-dev libstdc++-12-dev
```
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer lists packages (clang, cmake, etc.) required for building Flutter desktop apps on Linux, which are found in Passage [2]. However, the reference answer lists packages (curl, git, unzip, etc.) required for the initial installation of the Flutter SDK itself. The assistant's answer does not match the reference answer's specific list of prerequisites for installing Flutter, although it is factually correct for a different stage of the process (desktop development setup). Since the question asks about installing Flutter, the reference is the correct target, making the assistant's answer inaccurate in this context, but faithful to the provided passages which discuss desktop tooling.

## q023 (single, en) retrieval_miss + low_accuracy

- **Soru:** My animations look janky. What should I check first when profiling?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/perf/rendering-performance
- **Beklenen sayfa derin aramada:** 5. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/tools/devtools/performance
  2. https://docs.flutter.dev/tools/devtools/release-notes/release-notes-2.17.0
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/tools/devtools/performance
- **Cevap:** Start by opening DevTools → Performance view and selecting the janky frames in the frames chart. Then disable the Render Clip, Render Opacity, and Render Physical Shape layer options one at a time to see if raster time drops, which indicates excessive clipping, opacity, or physical‑modeling effects are causing the jank. If performance improves, reduce or simplify those effects in your app.
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer focuses on specific debugging steps (disabling render layers) which are supported by the passages, but it completely misses the primary advice in the reference answer: ensuring the app is built in profile mode (not debug) and checking for UI rebuilds or large lists. The reference answer prioritizes the build mode and widget tree issues, whereas the assistant prioritizes rasterization effects, making it miss the main point of the reference.

## q026 (single, en) low_accuracy

- **Soru:** Which accessibility standards and regulations might apply to my Flutter app?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/ui/accessibility
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/ui/accessibility
  2. https://docs.flutter.dev/ui/accessibility/accessibility-testing
  3. https://docs.flutter.dev/resources/faq
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/ui/accessibility
- **Cevap:** The UN Convention on the Rights of Persons with Disabilities (CRPD) is cited as a key international standard that creates a moral and legal imperative for universal access, and many countries enforce accessibility requirements based on it. These regulations, together with any local accessibility laws, may apply to your Flutter app.
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer focuses on the UN CRPD, which is mentioned in the passages, but it completely misses the specific technical standards (WCAG 2, EN 301 549) and documentation templates (VPAT) listed in the reference answer. Therefore, it fails to answer the specific question about which standards apply, relying instead on general background information.

## q028 (single, en) low_accuracy

- **Soru:** In my iOS App Clip target, what do I add to Build Phases so the Dart code gets compiled?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/platform-integration/ios/ios-app-clip
- **Beklenen sayfa derin aramada:** 1. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/platform-integration/ios/ios-app-clip
  2. https://docs.flutter.dev/interop/bind-native-code
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/platform-integration/ios/ios-app-clip
- **Cevap:** Add a Run Script build phase at the end of the App Clip target and insert the command:
```bash
/bin/sh "$FLUTTER_ROOT/packages/flutter_tools/bin/xcode_backend.sh" embed_and_thin
```
Then uncheck “Based on dependency analysis”. This mirrors the main app target’s build phases and ensures the Flutter engine and Dart code are embedded in the App Clip bundle.
- **Judge:** doğruluk=2 sadakat=5 | The assistant's answer is incorrect regarding the specific command required. The reference answer and the provided passages (specifically passage [2]) indicate that the command should be `xcode_backend.sh embed_and_thin` for the App Clip target to ensure the Flutter engine and Dart code are embedded. However, the reference answer explicitly states the command should be `xcode_backend.sh build` (which is typically for the main app or a specific build step, but the prompt's reference answer is the ground truth here). Wait, looking closely at Passage [2], it says: "This time, add: ... embed_and_thin ... In other words, the same as the main app target's build phases." This implies the main app uses `build` (standard Flutter setup) and the App Clip uses `embed_and_thin`? Or does it mean the App Clip phase is the same *type* of phase? Let's re-read the reference answer: "Add a new Run Script Phase ... containing ... build". The assistant used `embed_and_thin`. Passage [2] explicitly shows `embed_and_thin` for the App Clip target. The reference answer says `build`. There is a contradiction between the Reference Answer and Passage [2]. However, the instructions say "accuracy: does the assistant's answer agree with the reference answer?". The assistant used `embed_and_thin`, the reference used `build`. Therefore, the assistant contradicts the reference answer. Additionally, the assistant claims this "mirrors the main app target's build phases", which Passage [2] supports ("In other words, the same as the main app target's build phases"), but the command itself differs from the reference. Since the reference is the ground truth for accuracy, the assistant is wrong on the command. Regarding faithfulness, the assistant's command `embed_and_thin` is found in Passage [2], so it is supported by the passages, even if it contradicts the reference answer. The reference answer might be describing a different step or the main app, but the question asks about the App Clip. Passage [2] is titled "Step 7" (implied by context of Step 8 following) and specifically discusses the App Clip target build phase, showing `embed_and_thin`. The reference answer says `build`. This is a conflict. Usually, `build` is for the main app and `embed_and_thin` is for the App Clip to avoid duplicating the engine if it's already in the main app, or vice versa. Given the strict instruction to grade accuracy against the reference, the assistant is inaccurate. Faithfulness: The assistant's claims are supported by Passage [2] (command, uncheck dependency analysis, mirrors main app).

## q032 (single, en) retrieval_miss

- **Soru:** How do I show a brief message at the bottom of the screen after an action?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/design/snackbars
- **Beklenen sayfa derin aramada:** 28. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/forms/retrieve-input
  2. https://docs.flutter.dev/learn/pathway/tutorial/navigation
  3. https://docs.flutter.dev/flutter-for/uikit-devs
  4. https://docs.flutter.dev/cookbook/lists/mixed-list
  5. https://docs.flutter.dev/ai/ai-toolkit/feature-integration
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/ai/ai-toolkit/feature-integration
- **Cevap:** Use the ScaffoldMessenger to display a SnackBar. Call ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Your message'))); where the text is the brief message you want to show. The SnackBar appears at the bottom of the screen for a short duration and then disappears automatically.
- **Judge:** doğruluk=5 sadakat=5 | The assistant's answer correctly identifies the use of `ScaffoldMessenger.of(context).showSnackBar` with a `SnackBar` widget, which aligns perfectly with the reference answer. The specific code example and the description of the SnackBar appearing at the bottom and disappearing automatically are supported by Passage [5], which contains the exact code snippet and context for showing a SnackBar.

## q035 (single, en) retrieval_miss + refused

- **Soru:** How do I add a slide-out side navigation menu to a screen?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/design/drawer
- **Beklenen sayfa derin aramada:** 19. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/learn/pathway/tutorial/navigation
  2. https://docs.flutter.dev/ui/adaptive-responsive/platform-adaptations
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q041 (multi, en) retrieval_miss + refused

- **Soru:** How do I fetch a list of items from a REST API and show it in a scrollable list?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/networking/fetch-data, https://docs.flutter.dev/cookbook/lists/long-lists
- **Beklenen sayfa derin aramada:** 6. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/flutter-for/react-native-devs
  2. https://docs.flutter.dev/cookbook/lists/horizontal-list
  3. https://docs.flutter.dev/cookbook/testing/widget/scrolling
  4. https://docs.flutter.dev/ui/layout/scrolling
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q044 (multi, en) retrieval_miss + refused

- **Soru:** How do I test a widget that depends on a network call without hitting the real server?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/testing/unit/mocking, https://docs.flutter.dev/cookbook/testing/widget/introduction
- **Beklenen sayfa derin aramada:** 6. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/testing/integration/introduction
  2. https://docs.flutter.dev/testing/integration-tests
  3. https://docs.flutter.dev/tools/devtools/network
  4. https://docs.flutter.dev/flutter-for/xamarin-forms-devs
  5. https://docs.flutter.dev/flutter-for/uikit-devs
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q049 (multi, en) retrieval_miss

- **Soru:** How do I add a Flutter module to an existing iOS app and debug it?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/add-to-app/ios/project-setup, https://docs.flutter.dev/add-to-app/debugging
- **Beklenen sayfa derin aramada:** 5. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/add-to-app/ios/project-setup-legacy
  2. https://docs.flutter.dev/platform-integration/ios/app-extensions
  3. https://docs.flutter.dev/add-to-app
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/add-to-app/ios/project-setup-legacy, https://docs.flutter.dev/add-to-app
- **Cevap:** First create a Flutter module and embed it in your iOS project using the add‑to‑app methods (e.g., CocoaPods or framework integration) described in the documentation. Add a `FlutterEngine` in your host app and launch a `FlutterViewController` from it, then run the iOS app from Xcode in Debug mode. To debug the Flutter side, use `flutter attach` (or the IDE’s attach command) which enables hot‑reload and other debugging features while the app is running. Refer to the sample add‑to‑app projects for a complete workflow.
- **Judge:** doğruluk=5 sadakat=5 | The assistant's answer accurately reflects the reference answer by describing the integration of a Flutter module into an iOS app and the use of `flutter attach` for debugging. All specific technical details mentioned, such as using `FlutterEngine`, `FlutterViewController`, and the availability of sample projects, are supported by the provided passages (specifically passages [1] and [3]).

## q051 (multi, en) retrieval_miss

- **Soru:** How do I organize my app into layers and share state between screens with ChangeNotifier?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/app-architecture/guide, https://docs.flutter.dev/data-and-backend/state-mgmt/simple
- **Beklenen sayfa derin aramada:** 16. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/data-and-backend/state-mgmt/intro
  2. https://docs.flutter.dev/learn/pathway/tutorial/change-notifier
  3. https://docs.flutter.dev/learn/pathway/tutorial/listenable-builder
  4. https://docs.flutter.dev/app-architecture/case-study/ui-layer
  5. https://docs.flutter.dev/data-and-backend/state-mgmt/ephemeral-vs-app
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/data-and-backend/state-mgmt/intro, https://docs.flutter.dev/learn/pathway/tutorial/change-notifier, https://docs.flutter.dev/learn/pathway/tutorial/listenable-builder
- **Cevap:** Organize your app using an MVVM structure: keep your data and business logic in a Model layer, create a ViewModel layer that extends `ChangeNotifier` to hold the shared state, and place your UI in a View layer. In the ViewModel you expose the state you want to share and call `notifyListeners()` whenever it changes. In each screen’s widget tree, wrap the UI that depends on that state with a `ListenableBuilder` that listens to the same `ChangeNotifier` so the UI automatically rebuilds when the shared state updates.
- **Judge:** doğruluk=5 sadakat=5 | The assistant's answer accurately reflects the MVVM architecture described in the passages, specifically using ChangeNotifier in the ViewModel and ListenableBuilder in the View to share state. All technical claims (extending ChangeNotifier, calling notifyListeners, using ListenableBuilder) are directly supported by passages [2] and [3].

## q072 (tr, tr) retrieval_miss + refused

- **Soru:** Flutter SDK'yı bilgisayarımdan doğru şekilde nasıl kaldırırım?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/install/uninstall
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/tools/android-studio
  2. https://docs.flutter.dev/learn/pathway/tutorial/create-an-app
  3. https://docs.flutter.dev/install/archive
  4. https://docs.flutter.dev/platform-integration/android/setup
  5. https://docs.flutter.dev/resources/courses
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q073 (tr, tr) retrieval_miss + refused

- **Soru:** Kullanımdan kaldırılmış (deprecated) Flutter API'lerini kullanan kodu otomatik güncelleyen bir araç var mı?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/tools/flutter-fix
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/platform-integration/android/call-jetpack-apis
  2. https://docs.flutter.dev/cookbook/networking/background-parsing
  3. https://docs.flutter.dev/learn/pathway/tutorial/set-up-state-project
  4. https://docs.flutter.dev/flutter-for/xamarin-forms-devs
  5. https://docs.flutter.dev/flutter-for/android-devs
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q075 (tr, tr) retrieval_miss + refused

- **Soru:** iOS uygulamamın App Store'a yüklenecek paketini hangi komutla oluştururum ve çıktı nereye düşer?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/deployment/ios
- **Beklenen sayfa derin aramada:** 6. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/resources/in-app-purchases-overview
  2. https://docs.flutter.dev/platform-integration/linux/building
  3. https://docs.flutter.dev/deployment/macos
  4. https://docs.flutter.dev/resources/faq
  5. https://docs.flutter.dev/platform-integration/ios/apple-frameworks
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q076 (tr, tr) retrieval_miss

- **Soru:** Uygulamamın her yerinde özel bir yazı tipini (font) nasıl kullanırım?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/design/fonts
- **Beklenen sayfa derin aramada:** 7. sırada
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/ui/design/text/typography
  2. https://docs.flutter.dev/ui/internationalization
  3. https://docs.flutter.dev/cookbook/effects/shimmer-loading
  4. https://docs.flutter.dev/flutter-for/swiftui-devs
  5. https://docs.flutter.dev/flutter-for/compose-devs
- **Durum:** answered | kaynaklar: https://docs.flutter.dev/flutter-for/swiftui-devs, https://docs.flutter.dev/flutter-for/compose-devs
- **Cevap:** Öncelikle özel .ttf/.otf dosyanızı proje kökünde bir `fonts` klasörüne koyun ve `pubspec.yaml` dosyasının `flutter:` bölümüne şu şekilde ekleyin:
```yaml
flutter:
  fonts:
    - family: BungeeSpice
      fonts:
        - asset: fonts/BungeeSpice-Regular.ttf
```
Ardından, istediğiniz yerde `Text` widget'ına `fontFamily` değerini belirterek kullanabilirsiniz:
```dart
Text(
  'Örnek',
  style: TextStyle(fontFamily: 'BungeeSpice'),
);
```
- **Judge:** doğruluk=5 sadakat=5 | The assistant's answer correctly describes the process of adding a custom font in Flutter: placing the file in a `fonts` directory, declaring it in `pubspec.yaml` under the `flutter: fonts:` section, and using the `fontFamily` property in `TextStyle`. This aligns perfectly with the reference answer and is fully supported by Passage [4], which provides the exact steps and code snippets used in the response.

## q077 (tr, tr) retrieval_miss + refused

- **Soru:** Kullanıcının bir TextField'a yazdığı metni nasıl okurum?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/forms/retrieve-input
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/cookbook/forms/text-input
  2. https://docs.flutter.dev/ai/ai-toolkit/user-experience
  3. https://docs.flutter.dev/cookbook/effects/shimmer-loading
  4. https://docs.flutter.dev/ai/best-practices/prompting
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q078 (tr, tr) retrieval_miss + refused

- **Soru:** Bir işlemden sonra ekranın altında kısa bir mesaj nasıl gösteririm?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/design/snackbars
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/ui/accessibility
  2. https://docs.flutter.dev/ui/layout/tutorial
  3. https://docs.flutter.dev/ai/tools
  4. https://docs.flutter.dev/app-architecture/case-study/data-layer
  5. https://docs.flutter.dev/tools/android-studio
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q079 (tr, tr) retrieval_miss + refused

- **Soru:** Binlerce öğeli bir listeyi verimli şekilde nasıl gösteririm?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/cookbook/lists/long-lists
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/tools/android-studio
  2. https://docs.flutter.dev/packages-and-plugins/developing-packages
  3. https://docs.flutter.dev/ui/accessibility
  4. https://docs.flutter.dev/ui/internationalization
  5. https://docs.flutter.dev/ai/ai-toolkit/user-experience
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -

## q080 (tr, tr) retrieval_miss + refused

- **Soru:** Flutter SDK'mı en yeni sürüme nasıl güncellerim?
- **Aranan sorgu:** (soru olduğu gibi)
- **Beklenen sayfa(lar):** https://docs.flutter.dev/install/upgrade
- **Beklenen sayfa derin aramada:** ilk 50 içinde yok
- **Gelen sayfalar:**
  1. https://docs.flutter.dev/platform-integration/linux/building
  2. https://docs.flutter.dev/learn/pathway/tutorial/create-an-app
  3. https://docs.flutter.dev/ui/assets/asset-transformation
- **Durum:** not_found | kaynaklar: -
- **Cevap:** Bu sorunun cevabını Flutter dokümanında bulamadım. / I could not find the answer in the Flutter docs.
- **Judge:** doğruluk=None sadakat=None | -
