# Judge kalibrasyonu: elle puanlama formu

Her cevap için iki puan ver (1-5) ve `eval/human_scores.csv` dosyasına yaz. Judge'ın puanlarını görmüyorsun, bilerek. Ölçek judge'a verilenle aynıdır:

```
accuracy: does the assistant's answer agree with the reference answer?
5 = covers the key points of the reference, no contradictions
4 = correct, but misses a minor point
3 = partly correct, misses or blurs a main point
2 = mostly wrong, or misses the main point
1 = wrong, irrelevant, or contradicts the reference

faithfulness: is every claim in the assistant's answer supported by the passages?
5 = every claim is in the passages
4 = one minor detail is not in the passages
3 = several claims are not in the passages
2 = most claims are not in the passages
1 = the answer contradicts or ignores the passages
A claim that is true but is not in the passages still counts as unsupported: it came from the model's memory, not from the docs.
```

---
## 1. (id: q036)

**Soru:** How can I save a small value like a counter so it survives app restarts?

**Referans cevap:** Use the shared_preferences package to store key-value data on disk (for example setInt and getInt).

**Sistemin cevabı:** Add the `shared_preferences` package to your project and import it. On startup obtain the instance with `await SharedPreferences.getInstance()`, read the saved integer with `prefs.getInt('counter') ?? 0`, and after each change store it using `prefs.setInt('counter', _counter)`. This writes the value to disk so it is available after the app is closed and reopened. Example:
```dart
final prefs = await SharedPreferences.getInstance();
_counter = prefs.getInt('counter') ?? 0;
await prefs.setInt('counter', _counter);
```

**Modele verilen pasajlar:**

[1] e> {
  int _counter = 0;

  @override
  void initState() {
    super.initState();
    _loadCounter();
  }

  /// Load the initial counter value from persistent storage on start,
  /// or fallback to 0 if it doesn't exist.
  Future<void> _loadCounter() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _counter = prefs.getInt('counter') ?? 0;
    });
  }

  /// After a click, increment the counter state and
  /// asynchronously save it to persistent storage.
  Future<void> _incrementCounter() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _counter = (prefs.getInt('counter') ?? 0) + 1;
      prefs.setInt('counter', _counter);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('You have p

[2] persistent key-value pairs that are global to the app?

In React Native, you use the `setItem` and `getItem` functions
of the `AsyncStorage` component to store and retrieve data
that is persistent and global to the app.

```js
// React Native
const [counter, setCounter] = useState(0)
...
await AsyncStorage.setItem( 'counterkey', json.stringify(++this.state.counter));
AsyncStorage.getItem('counterkey').then(value => {
  if (value != null) {
    setCounter(value);
  }
});
```

In Flutter, use the [`shared_preferences`][] plugin to
store and retrieve key-value data that is persistent and global
to the app. The `shared_preferences` plugin wraps
`NSUserDefaults` on iOS and `SharedPreferences` on Android,
providing a persistent store for simple data.

To add the `shared_preferences` package as a dependency, run `flutter pub add`:

```console
$ flutter pub add shared_preferences
```

```dart
import 'package:shared_preferences/shared_preferences.dart';
```

To implement persistent data, use th

[3] counter key-value pair from persistent storage.
await prefs.remove('counter');
```

## Supported types

Although the key-value storage provided by `shared_preferences` is
easy and convenient to use, it has limitations:

* Only primitive types can be used: `int`, `double`, `bool`, `String`,
  and `List<String>`.
* It's not designed to store large amounts of data.
* There is no guarantee that data will be persisted across app restarts.

## Testing support

It's a good idea to test code that persists data using `shared_preferences`.
To enable this, the package provides an
in-memory mock implementation of the preference store.

To set up your tests to use the mock implementation,
call the `setMockInitialValues` static method in
a `setUpAll()` method in your test files.
Pass in a map of key-value pairs to use as the initial values.

```dart
SharedPreferences.setMockInitialValues(<String, Object>{'counter': 2});
```

## Complete example

```dart
import 'package:material_ui/material_ui.dart';

[4] arse(contents);
    } catch (_) {
      // If an error was encountered, return 0.
      return 0;
    }
  }

  Future<File> writeCounter(int counter) async {
    final file = await _localFile;

    // Write the counter as a string to the file.
    return file.writeAsString('$counter');
  }
}

class FlutterDemo extends StatefulWidget {
  const FlutterDemo({super.key, required this.storage});

  final CounterStorage storage;

  @override
  State<FlutterDemo> createState() => _FlutterDemoState();
}

class _FlutterDemoState extends State<FlutterDemo> {
  int _counter = 0;

  @override
  void initState() {
    super.initState();
    widget.storage.readCounter().then((value) {
      setState(() {
        _counter = value;
      });
    });
  }

  Future<File> _incrementCounter() {
    setState(() {
      _counter++;
    });

    // Write the variable as a string to the file.
    return widget.storage.writeCounter(_counter);
  }

  @override
  Widget build(BuildContext context) {
    return S

[5] storage under the 'counter' key.
await prefs.setInt('counter', counter);
```

## 3. Read data

To read data, use the appropriate getter method provided by the
`SharedPreferences` class. For each setter there is a corresponding getter.
For example, you can use the `getInt`, `getBool`, and `getString` methods.

```dart
final prefs = await SharedPreferences.getInstance();

// Try reading the counter value from persistent storage.
// If not present, null is returned, so default to 0.
final counter = prefs.getInt('counter') ?? 0;
```

Note that the getter methods throw an exception if the persisted value
has a different type than the getter method expects.

## 4. Remove data

To delete data, use the `remove()` method.

```dart
final prefs = await SharedPreferences.getInstance();

// Remove the counter key-value pair from persistent storage.
await prefs.remove('counter');
```

## Supported types

Although the key-value storage provided by `shared_preferences` is
easy and convenient to use, i

---
## 2. (id: q049)

**Soru:** How do I add a Flutter module to an existing iOS app and debug it?

**Referans cevap:** Integrate the Flutter module into the iOS project (CocoaPods or the documented project setup), then debug by launching the host app and running flutter attach.

**Sistemin cevabı:** First create a Flutter module and embed it in your iOS project using the add‑to‑app methods (e.g., CocoaPods or framework integration) described in the documentation. Add a `FlutterEngine` in your host app and launch a `FlutterViewController` from it, then run the iOS app from Xcode in Debug mode. To debug the Flutter side, use `flutter attach` (or the IDE’s attach command) which enables hot‑reload and other debugging features while the app is running. Refer to the sample add‑to‑app projects for a complete workflow.

**Modele verilen pasajlar:**

[1] ing the module on a new machine,
  run `flutter pub get` in the `my_flutter` directory.
  This regenerates the `.ios/` directory before building
  the iOS project that uses the Flutter module.

## Embed a Flutter module in your iOS app

After you have developed your Flutter module,
you can embed it using the methods described
in the table at the top of the page.

You can run in **Debug** mode on a simulator or a real device,
and **Release** mode on a real device.

Learn more about [Flutter's build modes][build modes of Flutter].

To use Flutter debugging features such as hot reload,
consult [Debugging your add-to-app module][].

<Tabs key="darwin-deps">
<Tab name="Use CocoaPods">

</Tab>
<Tab name="Use frameworks">

</Tab>
<Tab name="Use frameworks and CocoaPods">

</Tab>
</Tabs>

## Set local network privacy permissions

## Mitigate known issue with Apple Silicon Macs

On [Macs running Apple Silicon][apple-silicon],
the host app builds for an `arm64` simulator.
While Flutter supports 

[2] [Apple's app extension documentation]: /app-extensions/
[Test your app with the simulator]: #test-extensions
[Share]: /library/archive/documentation/General/Conceptual/ExtensibilityPG/Share.html

## Test an iOS app extension {: #test-extensions }

After you've added an app extension to your Flutter project,
you can test it, using a simulator or physical device.
If you are testing you extension in debug mode, you must
use the iOS simulator.

The following steps assume you're using the sample
application and Share extension from
[Adding iOS app extensions][].

<Tabs key="register-plugins-tabs" wrapped="true">

<Tab name="Simulator">

1.  In Xcode, [add an app extension to your project][].

1.  In the console, use the following command to run your
    iOS app:

    ```console
    $ flutter run
    ```

1.  In the simulator, test your app extension.

    *   Launch an app that supports the Share extension,
        such as the Photos app.

    *   Select a photo, tap the share button, then 

[3]  steps on iOS" />

* Build your Flutter module into a Swift package
  for integration into your own build system.
* Auto-build and import the Flutter module using Xcode build phases.
* [`FlutterEngine`][ios-engine] API for starting and persisting
  your Flutter environment independently of attaching a
  [`FlutterViewController`][].
* Objective-C and Swift host apps supported.
* Flutter modules can use [Flutter plugins][] to interact
  with the platform.
* Support for Flutter debugging and stateful hot reload by
  using `flutter attach` from IDEs or the command line to
  connect to an app that contains Flutter.

See our [add-to-app GitHub Samples repository][]
for sample projects in Android and iOS that import
a Flutter module for UI.

### Add to macOS applications
* Build your Flutter module into a Swift package
  for integration into your own build system.
* Auto-build and import the Flutter module using Xcode build phases.
* [`FlutterEngine`][macos-engine] API for starting and persis

[4] code should be added to the `lib/` directory.
Your Flutter dependencies, packages, and plugins must be added to the
`pubspec.yaml` file.

The `.ios/` hidden subfolder contains an Xcode workspace where
you can run a standalone version of your module.
This wrapper project bootstraps your Flutter code.
It contains helper scripts to facilitate building frameworks or
embedding the module into your existing application with CocoaPods.

* Add custom iOS code to your own existing application's
  project or to a plugin, not to the module's `.ios/`
  directory. Changes made in your module's `.ios/`
  directory don't appear in your existing iOS project
  using the module, and might be overwritten by Flutter.

* Exclude the `.ios/` directory from source control as
  it's autogenerated.

* Before building the module on a new machine,
  run `flutter pub get` in the `my_flutter` directory.
  This regenerates the `.ios/` directory before building
  the iOS project that uses the Flutter module.

## Emb

[5] nsion. In this example, the app extension
scheme is called `ShareExtension`, the Flutter app scheme is
called `Runner`, and the Flutter app is called
`Example App With Extension`:

1.  [Add an extension to your Flutter app][] if you haven't
    already done so.

1.  In Xcode, link Flutter plugins to your app extension target.

    <Tabs key="plugin-dependency-manager" wrapped="true">

    <Tab name="Swift Package Manager (default)">

    *   Open the **project navigator**
        (**View** > **Navigators** > **Project**).

    *   In the main window under **TARGETS**, select
        **ShareExtension**.

    *   Open the **General** tab.

    *   Under **Frameworks, Libraries, and Embedded Content**,
        click **+**.

    *   Select `FlutterGeneratedPluginSwiftPackage` and click **Add**.
        If it doesn't appear in the list,
        click **Add Other... > Add Package Dependency...**,
        click **Add Local...**, navigate to
        `ios/Flutter/ephemeral/Packages/FlutterGener

---
## 3. (id: q037)

**Soru:** How do I connect my app to a WebSocket server and listen to messages?

**Referans cevap:** Add the web_socket_channel package, connect with WebSocketChannel.connect, listen to channel.stream (for example with a StreamBuilder), send with channel.sink.add, and close the sink when done.

**Sistemin cevabı:** Create a `WebSocketChannel` with `WebSocketChannel.connect(Uri.parse('wss://echo.websocket.org'))`. Then listen to incoming messages by using the channel’s `stream`, for example with a `StreamBuilder` that rebuilds a `Text` widget when `snapshot.hasData` is true. You can also add listeners directly to `channel.stream` if you prefer not to use a widget. Remember to close the channel with `channel.sink.close()` when done.

**Modele verilen pasajlar:**

[1] In addition to normal HTTP requests,
you can connect to servers using `WebSockets`.
`WebSockets` allow for two-way communication with a server
without polling.

In this example, connect to a [test WebSocket server][].
The server sends back the same message you send to it.
This recipe uses the following steps:

  1. Connect to a WebSocket server.
  2. Listen for messages from the server.
  3. Send data to the server.
  4. Close the WebSocket connection.

## 1. Connect to a WebSocket server

The [`web_socket_channel`][] package provides the
tools you need to connect to a WebSocket server.

The package provides a `WebSocketChannel`
that allows you to both listen for messages
from the server and push messages to the server.

In Flutter, use the following line to
create a `WebSocketChannel` that connects to a server:

```dart
final WebSocketChannel channel = WebSocketChannel.connect(
  Uri.parse('wss://echo.websocket.org'),
);
```

## 2. Listen for messages from the server

Now that you've 

[2] t connects to a server:

```dart
final WebSocketChannel channel = WebSocketChannel.connect(
  Uri.parse('wss://echo.websocket.org'),
);
```

## 2. Listen for messages from the server

Now that you've established a connection,
listen to messages from the server.

After sending a message to the test server,
it sends the same message back.

In this example, use a [`StreamBuilder`][]
widget to listen for new messages, and a
[`Text`][] widget to display them.

```dart
StreamBuilder(
  stream: channel.stream,
  builder: (context, snapshot) {
    return Text(snapshot.hasData ? '${snapshot.data}' : '');
  },
),
```

### How this works

The `WebSocketChannel` provides a
[`Stream`][] of messages from the server.

The `Stream` class is a fundamental part of the `dart:async` package.
It provides a way to listen to async events from a data source.
Unlike `Future`, which returns a single async response,
the `Stream` class can deliver many events over time.

The [`StreamBuilder`][] widget connects to

[3]  to listen to async events from a data source.
Unlike `Future`, which returns a single async response,
the `Stream` class can deliver many events over time.

The [`StreamBuilder`][] widget connects to a `Stream`
and asks Flutter to rebuild every time it
receives an event using the given `builder()` function.

## 3. Send data to the server

To send data to the server,
`add()` messages to the `sink` provided
by the `WebSocketChannel`.

```dart
channel.sink.add('Hello!');
```

### How this works

The `WebSocketChannel` provides a
[`StreamSink`][] to push messages to the server.

The `StreamSink` class provides a general way to add sync or async
events to a data source.

## 4. Close the WebSocket connection

After you're done using the WebSocket, close the connection:

```dart
channel.sink.close();
```

## Complete example

```dart
import 'package:material_ui/material_ui.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() => runApp(const MyApp());

class MyApp 

[4] ur A2A server URL.
          url: Uri.parse('http://localhost:8080'),
        );
        _uiAgent = Conversation(
          controller: _surfaceController,
          transport: _transportAdapter,
        );

        // Listen for messages from the remote agent.
        _connector.stream.listen(_surfaceController.handleMessage);

      }

      @override
      void dispose() {
        _textController.dispose();
        _uiAgent.dispose();
        _transportAdapter.dispose();
        _surfaceController.dispose();
        _connector.dispose();
        super.dispose();
      }

      void _handleSubmitted(String text) async {
        if (text.isEmpty) return;
        _textController.clear();
        final message = ChatMessage.user(text);
        setState(() {
          _messages.insert(0, message);
        });
        
        final responseText = await _connector.connectAndSend(message);
        
        // Handling response depends on your app's logic
      }

      @override
      Widg

[5] vePort.sendPort);

    // The 'echo' isolate sends its SendPort as the first message.
    SendPort sendPort = await receivePort.first as SendPort;

    final msg = await sendReceive(
      sendPort,
      'https://jsonplaceholder.typicode.com/posts',
    ) as List<Object?>;
    final posts = msg.cast<Map<String, Object?>>();

    setState(() {
      widgets = posts;
    });
  }

  // The entry point for the isolate.
  static Future<void> dataLoader(SendPort sendPort) async {
    // Open the ReceivePort for incoming messages.
    ReceivePort port = ReceivePort();

    // Notify any other isolates what port this isolate listens to.
    sendPort.send(port.sendPort);

    await for (var msg in port) {
      String dataUrl = msg[0] as String;
      SendPort replyTo = msg[1] as SendPort;

      http.Response response = await http.get(Uri.parse(dataUrl));
      // Lots of JSON to parse
      replyTo.send(jsonDecode(response.body));
    }
  }

  Future<Object?> sendReceive(SendPort port, Objec

---
## 4. (id: q029)

**Soru:** How do I use a custom font throughout my app?

**Referans cevap:** Add the font files as assets, declare them under flutter: fonts: in pubspec.yaml with a family name, then set fontFamily in a TextStyle (or the app theme).

**Sistemin cevabı:** First create a `fonts` folder in your project and copy the `.ttf` (or `.otf`) files there. Then open `pubspec.yaml` and add the font under the `flutter:` section, for example:
```yaml
flutter:
  fonts:
    - family: MyFont
      fonts:
        - asset: fonts/MyFont-Regular.ttf
```After the font is declared you can apply it throughout the app by using `TextStyle(fontFamily: 'MyFont')` in your widgets, or by setting the `fontFamily` in your app's theme to make it the default for all text. This will cause every `Text` widget to render with the custom font unless you override it locally.

**Modele verilen pasajlar:**

[1] Rather than declaring a font as part of an app,
you can declare a font as part of a separate package.
This is a convenient way to share the same font across
several different projects,
or for coders publishing their packages to [pub.dev][].
This recipe uses the following steps:

  1. Add a font to a package.
  2. Add the package and font to the app.
  3. Use the font.

Check out the [google_fonts][] package for direct access
to almost 1000 open-sourced font families.

## 1. Add a font to a package

To export fonts, place the files in your package's `lib` directory
or one of its subdirectories.
This example uses `lib/fonts` in a Flutter package named `awesome_package`.
Place the package directory next to your app directory.

<FileTree>

- awesome_package/
  - lib/
    - awesome_package.dart
    - fonts/
      - Raleway-Regular.ttf
      - Raleway-Italic.ttf
  - pubspec.yaml

</FileTree>

## 2. Add the package and fonts to the app

Now you can use the fonts in the package by
updating the

[2] * How to choose a font.
* How to import font files.
* How to set a font as a default.
* How to use a font in a given widget.

Although Android and iOS offer high quality system fonts,
designers want support for custom fonts.
You might have a custom-built font from a designer,
or perhaps you downloaded a font from [Google Fonts][].

A typeface is the collection of glyphs or shapes that comprise
a given style of lettering.
A font is one representation of that typeface at a given weight or variation.
Roboto is a typeface and Roboto Bold is a font.

Flutter lets you apply a custom font across an entire app or to individual widgets.
This recipe creates an app that uses custom fonts with the following steps.

1. Choose your fonts.
1. Import the font files.
1. Declare the font in the pubspec.
1. Set a font as the default.
1. Use a font in a specific widget.

You don't need to follow each step as you go.
The guide offers completed example files at the end.

This guide makes the following presu

[3] nd fonts improved over time.

Which font you should use depends on the following considerations.

* How much variation you need for fonts in your app?
* How much file size you can accept fonts using in your app?
* How many languages you need to support in your app?

Research what options a given font offers,
like more than one weight or style per font file,
[variable font capability][variable-fonts],
the availability of multiple font files for a multiple font weights,
or more than one width per font.

Choose the typeface or font family that meets the design needs of your app.

To learn how to get direct access to over 1,000 open-sourced font families,
check out the [google_fonts][] package.

<YouTubeEmbed id="8Vzv2CdbEY0"
  title="google_fonts | Flutter package of the week"></YouTubeEmbed>

To learn about another approach to using custom fonts that allows you to
re-use one font over multiple projects,
check out [Export fonts from a package][].

## Import the font files

To work with a 

[4] boto Mono sample',
             style: TextStyle(fontFamily: 'RobotoMono'),
           ),
         ),
       );
     }
   }
   ```

The resulting Flutter app should display the following screen.

![Custom Fonts Demo](/assets/images/docs/cookbook/fonts.png){:.site-mobile-screenshot}

[variable-fonts]: https://fonts.google.com/knowledge/introducing_type/introducing_variable_fonts
[Export fonts from a package]: /cookbook/design/package-fonts
[`fontFamily`]: /flutter/painting/TextStyle/fontFamily.html
[fontStyle property]: /flutter/painting/TextStyle/fontStyle.html
[`FontStyle`]: /flutter/dart-ui/FontStyle.html
[fontWeight property]: /flutter/painting/TextStyle/fontWeight.html
[`FontWeight`]: /flutter/dart-ui/FontWeight-class.html
[Google Fonts]: https://fonts.google.com
[google_fonts]: /google_fonts
[`TextStyle`]: /flutter/painting/TextStyle-class.html
[Using Themes to share colors and font styles]: /cookbook/design/themes

[5]  font file to your SwiftUI project. After adding the file,
use the `.font()` modifier to apply it to your UI components.

```swift
Text("Hello")
  .font(
    Font.custom(
      "BungeeSpice-Regular",
      size: 40
    )
  )
```

In **Flutter**, you control your resources with a file
named `pubspec.yaml`. This file is platform agnostic.
To add a custom font to your project, follow these steps:

1. Create a folder called `fonts` in the project's root directory.
   This optional step helps to organize your fonts.
1. Add your `.ttf`, `.otf`, or `.ttc` font file into the `fonts` folder.
1. Open the `pubspec.yaml` file within the project.
1. Find the `flutter` section.
1. Add your custom font(s) under the `fonts` section.

    ```yaml
    flutter:
      fonts:
        - family: BungeeSpice
          fonts:
            - asset: fonts/BungeeSpice-Regular.ttf
    ```

After you add the font to your project, you can use it as in the
following example:

```dart
Text(
  'Cupertino',
  style: Text

---
## 5. (id: q031)

**Soru:** How do I let users swipe a list item away to delete it?

**Referans cevap:** Wrap each list item in a Dismissible widget with a unique key and an onDismissed callback that removes the item from the data source.

**Sistemin cevabı:** Create a list of items and build it with ListView.builder. Wrap each list tile in a `Dismissible` widget, give it a unique `Key`, and supply an `onDismissed` callback that removes the item from the list (e.g., `items.removeAt(index)`) and optionally shows a SnackBar. Add a `background` (e.g., a red Container) to indicate the swipe action.

**Modele verilen pasajlar:**

[1] i + 1}');
```

### Convert the data source into a list

Display each item in the list on screen. Users won't
be able to swipe these items away just yet.

```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ListTile(title: Text(items[index]));
  },
)
```

## 2. Wrap each item in a Dismissible widget

In this step,
give users the ability to swipe an item off the list by using the
[`Dismissible`][] widget.

After the user has swiped away the item,
remove the item from the list and display a snackbar.
In a real app, you might need to perform more complex logic,
such as removing the item from a web service or database.

Update the `itemBuilder()` function to return a `Dismissible` widget:

```dart
itemBuilder: (context, index) {
  final item = items[index];
  return Dismissible(
    // Each Dismissible must contain a Key. Keys allow Flutter to
    // uniquely identify widgets.
    key: Key(item),
    // Provide a function that tells the app
    

[2] The "swipe to dismiss" pattern is common in many mobile apps.
For example, when writing an email app,
you might want to allow a user to swipe away
email messages to delete them from a list.

Flutter makes this task easy by providing the
[`Dismissible`][] widget.
Learn how to implement swipe to dismiss with the following steps:

  1. Create a list of items.
  2. Wrap each item in a `Dismissible` widget.
  3. Provide "leave behind" indicators.

## 1. Create a list of items

First, create a list of items. For detailed
instructions on how to create a list,
follow the [Working with long lists][] recipe.

### Create a data source

In this example,
you want 20 sample items to work with.
To keep it simple, generate a list of strings.

```dart
final items = List<String>.generate(20, (i) => 'Item ${i + 1}');
```

### Convert the data source into a list

Display each item in the list on screen. Users won't
be able to swipe these items away just yet.

```dart
ListView.builder(
  itemCount: items.l

[3] d background as the item is swiped away.
              background: Container(color: Colors.red),
              child: ListTile(title: Text(item)),
            );
          },
        ),
      ),
    );
  }
}
```

<noscript>
  <img src="/assets/images/docs/cookbook/dismissible.webp" alt="Dismissible Demo" class="site-mobile-screenshot" />
</noscript>

[`Dismissible`]: /flutter/widgets/Dismissible-class.html
[Working with long lists]: /cookbook/lists/long-lists

[4] unt: items.length,
          itemBuilder: (context, index) {
            final item = items[index];
            return Dismissible(
              // Each Dismissible must contain a Key. Keys allow Flutter to
              // uniquely identify widgets.
              key: Key(item),
              // Provide a function that tells the app
              // what to do after an item has been swiped away.
              onDismissed: (direction) {
                // Remove the item from the data source.
                setState(() {
                  items.removeAt(index);
                });

                // Then show a snackbar.
                ScaffoldMessenger.of(context)
                    .showSnackBar(SnackBar(content: Text('$item dismissed')));
              },
              // Show a red background as the item is swiped away.
              background: Container(color: Colors.red),
              child: ListTile(title: Text(item)),
            );
          },
        ),
      ),
    )

[5] [index];
  return Dismissible(
    // Each Dismissible must contain a Key. Keys allow Flutter to
    // uniquely identify widgets.
    key: Key(item),
    // Provide a function that tells the app
    // what to do after an item has been swiped away.
    onDismissed: (direction) {
      // Remove the item from the data source.
      setState(() {
        items.removeAt(index);
      });

      // Then show a snackbar.
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$item dismissed')));
    },
    child: ListTile(title: Text(item)),
  );
},
```

## 3. Provide "leave behind" indicators

As it stands,
the app allows users to swipe items off the list, but it doesn't
give a visual indication of what happens when they do.
To provide a cue that items are removed,
display a "leave behind" indicator as they
swipe the item off the screen. In this case,
the indicator is a red background.

To add the indicator,
provide a `background` parameter to the `Dismissible

---
## 6. (id: q033)

**Soru:** What's the efficient way to display a list with thousands of items?

**Referans cevap:** Use ListView.builder, which builds items lazily as they scroll into view instead of creating all children up front.

**Sistemin cevabı:** Use a lazy list such as `ListView.builder`, which builds only the visible items as you scroll. This avoids creating all widgets at once and works efficiently with thousands of entries. Example:
```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => Text(items[index]),
);
```

**Modele verilen pasajlar:**

[1] nd lists are implemented
might be causing performance problems for your app.
This section describes an important best
practice when creating grids and lists,
and how to determine whether your app uses
excessive layout passes.

#### Be lazy!

When building a large grid or list,
use the lazy builder methods, with callbacks.
That ensures that only the visible portion of the
screen is built at startup time.

For more information and examples, check out:

* [Working with long lists][]
* [Creating a `ListView` that loads one page at a time][]
  a community article by AbdulRahman AlHamali
* [`ListView.builder`][] API

[Creating a `ListView` that loads one page at a time]: https://medium.com/saugo360/flutter-creating-a-listview-that-loads-one-page-at-a-time-c5c91b6fabd3
[`ListView.builder`]: /flutter/widgets/ListView/ListView.builder.html
[Working with long lists]: /cookbook/lists/long-lists

#### Avoid intrinsics

For information on how intrinsic passes might be causing
problems with your gri

[2] The standard [`ListView`][] constructor works well
for small lists. To work with lists that contain
a large number of items, it's best to use the
[`ListView.builder`][] constructor.

In contrast to the default `ListView` constructor, which requires
creating all items at once, the `ListView.builder()` constructor
creates items as they're scrolled onto the screen.

## 1. Create a data source

First, you need a data source. For example, your data source
might be a list of messages, search results, or products in a store.
Most of the time, this data comes from the internet or a database.

For this example, generate a list of 10,000 Strings using the
[`List.generate`][] constructor.

```dart
List<String>.generate(10000, (i) => 'Item $i'),
```

## 2. Convert the data source into widgets

To display the list of strings, render each String as a widget
using `ListView.builder()`.
In this example, display each String on its own line.

```dart
ListView.builder(
  itemCount: items.length,
  protot

[3]  a list with a large number of items, `LazyList` has better
performance. It only lays out the components that will be visible
versus all of them.

```kotlin
data class Person(val name: String)

val people = arrayOf(
   Person(name = "Person 1"),
   Person(name = "Person 2"),
   Person(name = "Person 3")
)

@Composable
fun ListDemo(people: List<Person>) {
   Column {
      people.forEach {
         Text(it.name)
      }
   }
}

@Composable
fun ListDemo2(people: List<Person>) {
   LazyColumn {
      items(people) { person ->
         Text(person.name)
      }
   }
}
```

To lazily build a list in Flutter, ....

```dart
class Person {
  String name;
  Person(this.name);
}

var items = [
  Person('Person 1'),
  Person('Person 2'),
  Person('Person 3'),
];

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListView.builder(
        itemCount: items.length,
        itemBuilder: (context

[4] ommended, efficient,
and effective way to build a list uses a `ListView.Builder`.
This method is great when you have a dynamic
list or a list with very large amounts of data.

```dart
import 'dart:developer' as developer;

import 'package:material_ui/material_ui.dart';

void main() {
  runApp(const SampleApp());
}

class SampleApp extends StatelessWidget {
  const SampleApp({super.key});
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return const MaterialApp(title: 'Sample App', home: SampleAppPage());
  }
}

class SampleAppPage extends StatefulWidget {
  const SampleAppPage({super.key});

  @override
  State<SampleAppPage> createState() => _SampleAppPageState();
}

class _SampleAppPageState extends State<SampleAppPage> {
  List<Widget> widgets = [];

  @override
  void initState() {
    super.initState();
    for (int i = 0; i < 100; i++) {
      widgets.add(getRow(i));
    }
  }

  Widget getRow(int i) {
    return GestureDete

[5] ow(widgets.length));
          developer.log('Row $index');
        });
      },
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Text('Row $index'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sample App')),
      body: ListView(children: widgets),
    );
  }
}
```

The recommended, efficient, and effective way to build a list
uses a `ListView.Builder`.
This method is great when you have a dynamic list
or a list with very large amounts of data.
This is essentially the equivalent of RecyclerView on Android,
which automatically recycles list elements for you:

```dart
import 'dart:developer' as developer;

import 'package:material_ui/material_ui.dart';

void main() {
  runApp(const SampleApp());
}

class SampleApp extends StatelessWidget {
  /// This widget is the root of your application.
  const SampleApp({super.key});

  @override
  Widget build(BuildContext context

---
## 7. (id: q012)

**Soru:** How do I set up ChromeDriver to run Flutter integration tests in a browser?

**Referans cevap:** Install it with npx @puppeteer/browsers install chromedriver@stable, add its directory to your PATH, then verify with chromedriver --version.

**Sistemin cevabı:** First install ChromeDriver (for example with `npx @puppeteer/browsers install chromedriver@stable`) and add its directory to your `$PATH`. Verify the installation (`chromedriver --version`) and start the driver (`chromedriver --port=4444`). Then run the integration test from the project root, e.g.:
```bash
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  -d chrome
```

**Modele verilen pasajlar:**

[1] Launch `chromedriver` as follows:

   ```console
   $ chromedriver --port=4444
   ```

1. From the root of the project, run the following command:

   ```console
   $ flutter drive \
     --driver=test_driver/integration_test.dart \
     --target=integration_test/app_test.dart \
     -d chrome
   ```

   The response should resemble the following output:

   ```console
   Resolving dependencies...
     leak_tracker 10.0.0 (10.0.5 available)
     leak_tracker_flutter_testing 2.0.1 (3.0.5 available)
     leak_tracker_testing 2.0.1 (3.0.1 available)
     material_color_utilities 0.8.0 (0.11.1 available)
     meta 1.11.0 (1.14.0 available)
     test_api 0.6.1 (0.7.1 available)
     vm_service 13.0.0 (14.2.1 available)
   Got dependencies!
   7 packages have newer versions incompatible with dependency constraints.
   Try `flutter pub outdated` for more information.
   Launching integration_test/app_test.dart on Chrome in debug mode...
   Waiting for connection from debug service on Chrome..

[2] : https://www.npmjs.com/package/@puppeteer/browsers

1. Add the path to ChromeDriver to your `$PATH` environment variable.

1. Verify the ChromeDriver install succeeded.

   ```console
   $ chromedriver --version
   ChromeDriver 124.0.6367.60 (8771130bd84f76d855ae42fbe02752b03e352f17-refs/branch-heads/6367@{#798})
   ```

1. In your `counter_app` project directory,
   create a new directory named `test_driver`.

   ```console
   $ mkdir test_driver
   ```

1. In this directory, create a new file named `integration_test.dart`.

1. Copy the following code and paste it into your `integration_test.dart` file.

   
   ```dart title="test_driver/integration_test.dart"
   import 'package:integration_test/integration_test_driver.dart';
   
   Future<void> main() => integrationDriver();
   ```

1. Launch `chromedriver` as follows:

   ```console
   $ chromedriver --port=4444
   ```

1. From the root of the project, run the following command:

   ```console
   $ flutter drive \
     --driver=tes

[3] t.dart
   00:15 +0: loading /path/to/counter_app/integration_test/app_test.dart
   00:18 +0: loading /path/to/counter_app/integration_test/app_test.dart   2,387ms
   Xcode build done.                                           13.5s
   00:21 +1: All tests passed!
   ```

1. Verify that the test removed the Counter App when it finished.
   If not, subsequent tests fail. If needed, press on the app and choose
   **Remove App** from the context menu.

---

### Test in a web browser

To test in a web browser, perform the following steps.

1. Install [ChromeDriver][] into the directory of your choice.

   ```console
   $ npx @puppeteer/browsers install chromedriver@stable
   ```

   To simplify the install, this command uses the
   [`@puppeteer/browsers`][puppeteer] Node library.

   [puppeteer]: https://www.npmjs.com/package/@puppeteer/browsers

1. Add the path to ChromeDriver to your `$PATH` environment variable.

1. Verify the ChromeDriver install succeeded.

   ```console
   $ chromedriv

[4] endency constraints.
   Try `flutter pub outdated` for more information.
   Launching integration_test/app_test.dart on Chrome in debug mode...
   Waiting for connection from debug service on Chrome...             10.9s
   This app is linked to the debug service: ws://127.0.0.1:51523/3lofIjIdmbs=/ws
   Debug service listening on ws://127.0.0.1:51523/3lofIjIdmbs=/ws
   00:00 +0: end-to-end test tap on the floating action button, verify counter
   00:01 +1: (tearDownAll)
   00:01 +2: All tests passed!
   All tests passed.
   Application finished.
   ```

   To run this as a headless test, run `flutter drive`
   with `-d web-server` option:

   ```console
   $ flutter drive \
     --driver=test_driver/integration_test.dart \
     --target=integration_test/app_test.dart \
     -d web-server
   ```

To learn more, see the
[Running Flutter driver tests with web][] wiki page.

---

### Test in Firebase Test Lab (Android)

You can use Firebase Test Lab to test Android targets.

#### Android se

[5] makes integration tests similar to writing 
[widget tests][]. However, `integration_test` can't interact with
native platform UI.

- [patrol][] package: A popular third-party integration test package that
has many of the features supported by the `integration_test` package,
but can additionally interact with native platform UI such as
permission dialogs, notifications, or the contents of platform views.

## Terminology

**host machine**
: The system on which you develop your app, like a desktop computer.

**target device**
: The mobile device, browser, or desktop application that
  runs your Flutter app.

  If you run your app in a web browser or as a desktop application,
  the host machine and the target device are the same.

## Getting started

To use `integration_test`, add it as a dependency for your
Flutter app test file.

To migrate existing projects that use `flutter_driver`,
consult the [Migrating from flutter_driver][] guide.

To use `patrol`, follow the [Patrol setup guide][]

---
## 8. (id: q042)

**Soru:** How do I open a new screen with some data and get a value back when it closes?

**Referans cevap:** Pass the data to the new screen (through its constructor or route arguments) when calling Navigator.push, and return a result by passing it to Navigator.pop; await the push future to receive it.

**Sistemin cevabı:** Create the new screen widget so it receives the data you want to show (for example, via its constructor). When the user makes a choice, close the screen with `Navigator.of(context).pop(selectedValue);` to return that value. The original screen can await the navigation result (e.g., with `then` or `await`) and use the returned value, such as displaying it in a SnackBar. This pattern lets you both pass data to a screen and get a result back when it closes.

**Modele verilen pasajlar:**

[1] In some cases, you might want to return data from a new screen.
For example, say you push a new screen that presents two options to a user.
When the user taps an option, you want to inform the first screen
of the user's selection so that it can act on that information.

You can do this with the [`Navigator.pop()`][]
method using the following steps:

  1. Define the home screen
  2. Add a button that launches the selection screen
  3. Show the selection screen with two buttons
  4. When a button is tapped, close the selection screen
  5. Show a snackbar on the home screen with the selection

## 1. Define the home screen

The home screen displays a button. When tapped,
it launches the selection screen.

```dart
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Returning Data Demo')),
      // Create the SelectionButton widget in the next step.
      

[2]  back

In **SwiftUI**, you use the `dismiss` environment value to pop-back to
the previous screen.

```swift
Button("Pop back") {
  dismiss()
}
```

In **Flutter**, use the `pop()` function of the `Navigator` class:

```dart dartpad="3c125ab2dfba9f4178aeaeb8619c5bea"
TextButton(
  onPressed: () {
    // This code allows the
    // view to pop back to its presenter.
    Navigator.of(context).pop();
  },
  child: const Text('Pop back'),
),
```

### Navigating to another app

In **SwiftUI**, you use the `openURL` environment variable to open a
URL to another application.

```swift
@Environment(\.openURL) private var openUrl

// View code goes here

Button("Open website") {
  openUrl(
    URL(
      string: "https://google.com"
    )!
  )
}
```

In **Flutter**, use the [`url_launcher`][] plugin.

```dart dartpad="695beba25fa8120d89c9960cb222e276"
CupertinoButton(
  onPressed: () async {
    await launchUrl(Uri.parse('https://google.com'));
  },
  const Text('Open website'),
),
```

## Them

[3] Often, you not only want to navigate to a new screen,
but also pass data to the screen as well.
For example, you might want to pass information about
the item that's been tapped.

Remember: Screens are just widgets.
In this example, create a list of todos.
When a todo is tapped, navigate to a new screen (widget) that
displays information about the todo.
This recipe uses the following steps:

  1. Define a todo class.
  2. Display a list of todos.
  3. Create a detail screen that can display information about a todo.
  4. Navigate and pass data to the detail screen.

## 1. Define a todo class

First, you need a simple way to represent todos. For this example,
create a class that contains two pieces of data: the title and description.

```dart
class Todo {
  final String title;
  final String description;

  const Todo(this.title, this.description);
}
```

## 2. Create a list of todos

Second, display a list of todos. In this example, generate
20 todos and show them using a ListView.
For

[4] oute from the navigation stack, returning to the previous screen.
      correct: true
      explanation: Pop removes the top route from the stack, revealing the screen beneath it.
    - text: Clears all routes and shows the home screen.
      correct: false
      explanation: That would require popUntil or pushAndRemoveUntil; pop removes only the top route.
    - text: Refreshes the current screen with new data.
      correct: false
      explanation: Pop navigates back; to refresh, you'd use setState or other state management.
</Quiz>

[5]  [Persistent storage architecture: SQL][].

## Example application: App with theme selection

The example application consists of a single screen with an app bar at the top,
a list of items, and a text field input at the bottom.

<img src='/assets/images/docs/cookbook/architecture/todo_app_light.png'
class="site-mobile-screenshot" alt="ToDo application in light mode" >

In the `AppBar`,
a `Switch` allows users to change between dark and light theme modes.
This setting is applied immediately and it’s stored in the device
using a key-value data storage service.
The setting is restored when the user starts the application again.

<img src='/assets/images/docs/cookbook/architecture/todo_app_dark.png'
class="site-mobile-screenshot" alt="ToDo application in dark mode" >

The full, runnable source-code for this example is
available in [`/examples/app-architecture/todo_data_service/`][].

## Storing theme selection key-value data

This functionality follows the recommended Flutter architecture

---
## 9. (id: q028)

**Soru:** In my iOS App Clip target, what do I add to Build Phases so the Dart code gets compiled?

**Referans cevap:** Add a new Run Script Phase below Dependencies containing /bin/sh "$FLUTTER_ROOT/packages/flutter_tools/bin/xcode_backend.sh" build, and uncheck 'Based on dependency analysis'.

**Sistemin cevabı:** Add a Run Script build phase at the end of the App Clip target and insert the command:
```bash
/bin/sh "$FLUTTER_ROOT/packages/flutter_tools/bin/xcode_backend.sh" embed_and_thin
```
Then uncheck “Based on dependency analysis”. This mirrors the main app target’s build phases and ensures the Flutter engine and Dart code are embedded in the App Clip bundle.

**Modele verilen pasajlar:**

[1] ry selected for the
normal app target.

This gives your App Clip target access to Flutter's
required build settings.

Set **iOS Deployment Target** to at least **16.0** to take advantage of the
15MB size limit.

<DashImage figure image="development/platform-integration/ios-app-clip/configuration.png" />

**4.2**

In the App Clip group's `Info.plist` file, set:

* `Build version string (short)` to `$(FLUTTER_BUILD_NAME)`
* `Bundle version` to `$(FLUTTER_BUILD_NUMBER)`

## Step 5 - Share code and assets

### Option 1 - Share everything

Assuming the intent is to show the same Flutter UI
in the standard app as in the App Clip,
share the same code and assets.

For each of the following: `Main.storyboard`, `Assets.xcassets`,
`LaunchScreen.storyboard`, `GeneratedPluginRegistrant.m`, and
`AppDelegate.swift` (and `Supporting Files/main.m` if using Objective-C),
select the file, then in the first tab of the inspector,
also include the App Clip target in the `Target Membership`
checkbox group.



[2] Leave it as the last phase.

This time, add:

```bash
/bin/sh "$FLUTTER_ROOT/packages/flutter_tools/bin/xcode_backend.sh" embed_and_thin
```

Uncheck **Based on dependency analysis**.

In other words,
the same as the main app target's build phases.

<DashImage figure image="development/platform-integration/ios-app-clip/xcode-backend-embed.png" />

This ensures that your Flutter app and engine are embedded
into the App Clip bundle.

## Step 8 - Integrate plugins

If your project uses Flutter plugins, integrate them with your App Clip target.

<Tabs key="plugin-dependency-manager">
<Tab name="Swift Package Manager (default)">

1.  In Xcode, add `FlutterGeneratedPluginSwiftPackage` to your App Clip target:

    1.  Open `ios/Runner.xcworkspace` in Xcode.
    1.  In the project navigator, select the **Runner** project.
    1.  Under **TARGETS**, select your App Clip target.
    1.  Open the **General** tab.
    1.  Under **Frameworks, Libraries, and Embedded Content**, click **+**.
    1. 

[3] 

If you don't use the `SceneDelegate.swift` file,
remove the reference to it in the `Info.plist`.

Open the `Info.plist` file in the App Clip group.
Delete the entire dictionary entry for
**Application Scene Manifest**.

<DashImage figure image="development/platform-integration/ios-app-clip/scene-manifest.png" />

## Step 4 - Share build configurations

This step isn't necessary for add-to-app projects
since add-to-app projects have their custom build
configurations and versions.

**4.1**

Back in the project settings,
select the project entry now rather than any targets.

In the **Info** tab, under the **Configurations**
expandable group, expand the
**Debug**, **Profile**, and **Release** entries.

For each, select the same value from the drop-down menu
for the App Clip target as the entry selected for the
normal app target.

This gives your App Clip target access to Flutter's
required build settings.

Set **iOS Deployment Target** to at least **16.0** to take advantage of the
15MB s

[4] OS-specific build files (like
`CMakeLists.txt` for Linux/Windows, `.podspec` for iOS/macOS, or `build.gradle`
for Android) to compile your native code.

The build hook uses `package:native_toolchain_c` to compile the C code into a
dynamic library. You can customize this file to build other native languages or
to download pre-compiled binaries.

## The Dart code

The Dart code defines the public API of the package.

### Generating the bindings

To bind to the native code, the template uses [`package:ffigen`][] to generate
bindings from the header file (`src/native_add.h`). The generation is configured
in `ffigen.yaml`.

This generates `lib/native_add_bindings_generated.dart`.

### Calling the native function

The generated bindings in `lib/native_add_bindings_generated.dart` contain
`@Native() external` functions. These functions are automatically resolved at
runtime against the code asset outputted by the build hook (which runs at build
time). This means there is no OS-specific logic r

[5]     use_frameworks!
    use_modular_headers!
    flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))

    target 'Runner'
    target '<name of your App Clip target>'
    ```

    At the top of the file,
    uncomment the `platform :ios` line and set the
    version to the lowest of the two targets' iOS
    Deployment Target.

    For add-to-app, replace:

    ```ruby
    target 'MyApp' do
      install_all_flutter_pods(flutter_application_path)
    end
    ```

    with:

    ```ruby
    target 'MyApp' do
      install_all_flutter_pods(flutter_application_path)
    end

    target '<name of your App Clip target>' do
      install_all_flutter_pods(flutter_application_path)
    end
    ```

1.  From the command line,
    enter your Flutter project's `ios` directory
    and install the pods:

    ```console
    cd ios
    pod install
    ```

</Tab>
</Tabs>

## Run

You can now run your App Clip target from Xcode by
selecting your App Clip target from the scheme drop-down,


---
## 10. (id: q074)

**Soru:** json_serializable kullanırsam serileştirme kodunu elle yazmam gerekmesin diye neyi otomatik üretir?

**Referans cevap:** A source code generator creates a file such as user.g.dart that contains all the necessary serialization logic, so you can forget manual JSON serialization in the class; the calling API (jsonDecode/jsonEncode) stays the same.

**Sistemin cevabı:** json_serializable, JSON serileştirme ve deserileştirme için gerekli boilerplate kodunu otomatik olarak üretir; bu kod genellikle model sınıfının yanındaki *.g.dart dosyasında toJson ve fromJson metodlarını içerir.

**Modele verilen pasajlar:**

[1] sing
[`JsonCodec`]: /dart-convert/JsonCodec-class.html
[`JsonSerializable`]: /documentation/json_annotation/latest/json_annotation/JsonSerializable-class.html
[`json_annotation`]: /packages/json_annotation
[`json_serializable`]: /packages/json_serializable
[`json_serializable` examples]: https://github.com/google/json_serializable.dart/blob/master/example/lib/example.dart
[pubspec file]: https://raw.githubusercontent.com/google/json_serializable.dart/master/example/pubspec.yaml
[reflection]: https://en.wikipedia.org/wiki/Reflection_(computer_programming)
[Serializing JSON manually using dart:convert]: #manual-encoding
[Serializing JSON using code generation libraries]: #code-generation
[tree shaking]: https://en.wikipedia.org/wiki/Tree_shaking
[Dive into Dart's patterns and records]: /codelabs/dart-patterns-records
[how to parse JSON in Dart/Flutter]: https://codewithandrea.com/articles/parse-json-dart/

[2] Since the serialization code is not handwritten or maintained manually
anymore, you minimize the risk of having JSON serialization exceptions at
runtime.

### Setting up json_serializable in a project

To include `json_serializable` in your project, you need one regular
dependency, and two _dev dependencies_. In short, _dev dependencies_
are dependencies that are not included in our app source code&mdash;they
are only used in the development environment.

To add the dependencies, run `flutter pub add`:

```console
$ flutter pub add json_annotation dev:build_runner dev:json_serializable
```

Run `flutter pub get` inside your project root folder
(or click **Packages get** in your editor)
to make these new dependencies available in your project.

### Creating model classes the json_serializable way

The following shows how to convert the `User` class to a
`json_serializable` class. For the sake of simplicity,
this code uses the simplified JSON model
from the previous samples.

**user.dart

[3] ult;

/// When `true` tell json_serializable that JSON must contain the key,
/// If the key doesn't exist, an exception is thrown.
@JsonKey(required: true)
final String id;

/// When `true` tell json_serializable that generated code should
/// ignore this field completely.
@JsonKey(ignore: true)
final String verificationCode;
```

### Running the code generation utility

When creating `json_serializable` classes the first time,
you'll get errors similar to the following:

```plaintext
Target of URI hasn't been generated: 'user.g.dart'.
```

These errors are entirely normal and are simply because the generated code for
the model class does not exist yet. To resolve this, run the code
generator that generates the serialization boilerplate.

There are two ways of running the code generator.

#### One-time code generation

By running `dart run build_runner build --delete-conflicting-outputs` in the project root,
you generate JSON serialization code for your models whenever they are needed.

[4]  were something that handled the JSON encoding
and decoding for you.  Luckily, there is!

<FragmentTarget id="code-generation" />

## Serializing JSON using code generation libraries

Although there are other libraries available, this guide uses
[`json_serializable`][], an automated source code generator that
generates the JSON serialization boilerplate for you.

You might have noticed two [Flutter Favorite][] packages
on pub.dev that generate JSON serialization code,
[`json_serializable`][] and [`built_value`][].
How do you choose between these packages?
The `json_serializable` package allows you to make regular
classes serializable by using annotations,
whereas the `built_value` package provides a higher-level way
of defining immutable value classes that can also be
serialized to JSON.

Since the serialization code is not handwritten or maintained manually
anymore, you minimize the risk of having JSON serialization exceptions at
runtime.

### Setting up json_serializable in a project

[5] It is hard to think of a mobile app that doesn't need to communicate with a
web server or easily store structured data at some point. When making
network-connected apps, the chances are that it needs to consume some good old
JSON, sooner or later.

This guide looks into ways of using JSON with Flutter.
It covers which JSON solution to use in different scenarios, and why.

_Encoding_ and _serialization_ are the same
thing&mdash;turning a data structure into a string.
_Decoding_ and _deserialization_ are the
opposite process&mdash;turning a string into a data structure.
However, _serialization_ also commonly refers to the entire process of
translating data structures to and from a more easily readable format.

To avoid confusion, this doc uses "serialization" when referring to the
overall process, and "encoding" and "decoding" when specifically
referring to those processes.

<YouTubeEmbed id="ngsxzZt5DoY" title="dart:convert (Technique of the Week)"></YouTubeEmbed>

## Which JSON seriali

---
## 11. (id: q045)

**Soru:** How do I set up separate dev and production builds for both Android and iOS?

**Referans cevap:** On Android define productFlavors in the Gradle configuration; on iOS create schemes and build configurations in Xcode; then run or build with --flavor <name>.

**Sistemin cevabı:** Create Flutter flavors such as `Debug-staging`/`Release-staging` for development and `Debug-production`/`Release-production` for production (see the flavor map in passage 3). In Xcode set a unique Product Bundle Identifier for each scheme (e.g., `com.example.flavorsExample.staging` for the staging scheme and `com.example.flavorsExample` for production) as described in passage 4, and add any build‑specific settings like API URLs in separate xcconfig files. Then build the appropriate flavor with the Flutter CLI (e.g., `flutter build appbundle` for Android or `flutter build ios --release --no-codesign --config-only` for iOS) and optionally automate distribution with a Fastfile lane as shown in passage 1.

**Modele verilen pasajlar:**

[1] Tunes/TestFlight.
1. Set up code signing.
    * ![Android](/assets/images/docs/cd/android.png) Follow the [Android app signing steps][].
    * ![iOS](/assets/images/docs/cd/ios.png) On iOS, create and sign using a
      distribution certificate instead of a development certificate when you're
      ready to test and deploy using TestFlight or App Store.
        * Create and download a distribution certificate in your
          [Apple Developer Account console][].
        * `open [project]/ios/Runner.xcworkspace/` and select the distribution
          certificate in your target's settings pane.
1. Create a `Fastfile` script for each platform.
    * ![Android](/assets/images/docs/cd/android.png) On Android, follow the
      [fastlane Android beta deployment guide][].
      Your edit could be as simple as adding a `lane` that calls
      `upload_to_play_store`.
      Set the `aab` argument to `../build/app/outputs/bundle/release/app-release.aab`
      to use the app bundle `flutter build`

[2] `flutter build appbundle` or
           `flutter build ios --release --no-codesign --config-only`,
           depending on the platform.
         * `cd android` or `cd ios`
         * `bundle exec fastlane [name of the lane]`

## Xcode Cloud

[Xcode Cloud][] is a continuous integration and delivery service for building,
testing, and distributing apps and frameworks for Apple platforms.

### Requirements

* Xcode 13.4.1 or higher.
* Be enrolled in the [Apple Developer Program][].

### Custom build script

Xcode Cloud recognizes [custom build scripts][] that can be
used to perform additional tasks at a designated time. It also includes a set
of [predefined environment variables][], such as `$CI_WORKSPACE`, which is the
location of your cloned repository.

The temporary build environment that Xcode Cloud uses includes tools that are
part of macOS and Xcode&mdash;for example, Python&mdash;and additionally Homebrew to
support installing third-party dependencies and tools.

#### Post-clone s

[3]   'Debug' => :debug,
      'Debug-staging' => :debug,
      'Debug-production' => :debug,
      'Profile' => :release,
      'Profile-staging' => :release,
      'Profile-production' => :release,
      'Release' => :release,
      'Release-staging' => :release,
      'Release-production' => :release,
      ...
    ```

### Add unique build settings

You can use [build settings][] to govern your iOS build
process from compilation and linking to debugging and
distribution. One way that you can use build settings
with Flutter flavors is to assign those build settings
to Xcode build configurations.
For example, you might want to assign different API URLs
to `Debug-staging` and `Debug-production`.
The following configurations show example build settings:

```plaintext title="debug-staging-settings.xcconfig"
# Debug-staging build settings
API_BASE_URL = staging.flavors.com/api
```

```plaintext title="debug-production-settings.xcconfig"
# Debug-production build settings
API_BASE_URL = flavor

[4] n one
version of the app (for example `staging`) without affecting
another version of the app (for example, `production`).

The following steps show how to set a unique
bundle identifier for two Xcode schemes called `staging`
and `production` in an iOS project called `flavors_example`.

1.  In Xcode, open the **project navigator**
    (**View > Navigators > Project**).

1.  In the main window under **TARGETS**, select
    **Runner**.

1.  Open the **Build Settings** tab.

1.  Navigate to the **Packaging** section.

1.  Expand the **Product Bundle Identifier** setting to
    view the different build configurations.

1.  For each scheme's build configuration, set the
    desired bundle identifier. For example:

    *   Debug-staging, Profile-staging, Release-staging:

        `com.example.flavorsExample.staging`

    *   Debug, Profile, Release, Debug-production,
        Profile-production, Release-production:

        `com.example.flavorsExample`

1.  Ensure that these bundle identifier

[5] dio.
1. Select **Open an existing Android Studio Project**
   in the **Welcome to Android Studio** dialog,
   or select **File > Open** from the menu,
   and select either the `hello/example/android/build.gradle`
   or the `hello/example/android/build.gradle.kts` file.
1. In the **Gradle Sync** dialog, select **OK**.
1. In the **Android Gradle Plugin Update** dialog,
   select **Don't remind me again for this project**.

The Android platform code of your plugin is located in
`hello/java/com.example.hello/HelloPlugin`.

You can run the example app from Android Studio by
pressing the run (&#9654;) button.

#### Step 2c: Add iOS platform code (.swift/.h+.m)

We recommend you edit the iOS code using Xcode.

Before editing the iOS platform code in Xcode,
first make sure that the code has been built at least once
(in other words, run the example app from your IDE/editor,
or in a terminal execute
`cd hello/example; flutter build ios --no-codesign --config-only`).

Then use the following steps

---
## 12. (id: q023)

**Soru:** My animations look janky. What should I check first when profiling?

**Referans cevap:** Make sure you profile an app built in profile mode, because the default debug mode isn't indicative of release performance. Then look for UI rebuilt far more than expected and large lists built directly instead of with ListView.

**Sistemin cevabı:** Start by opening DevTools → Performance view and selecting the janky frames in the frames chart. Then disable the Render Clip, Render Opacity, and Render Physical Shape layer options one at a time to see if raster time drops, which indicates excessive clipping, opacity, or physical‑modeling effects are causing the jank. If performance improves, reduce or simplify those effects in your app.

**Modele verilen pasajlar:**

[1] isable this option to check whether excessive
  use of physical modeling effects are affecting performance,
  such as shadows or elevation.
  If performance improves with this option disabled,
  try to reduce the use of physical modeling effects in your app.

![Screenshot of more debugging options](/assets/images/docs/tools/devtools/more-debugging-options.png)

## Import and export

DevTools supports importing and exporting performance snapshots.
Clicking the export button (upper-right corner above the
frame rendering chart) downloads a snapshot of the current data on the
performance page. To import a performance snapshot, you can drag and drop the
snapshot into DevTools from any page. **Note that DevTools only
supports importing files that were originally exported from DevTools.**

## Other resources

To learn how to monitor an app's performance and
detect jank using DevTools, check out a guided
[Performance View tutorial][performance-tutorial].

[GPU graph]: /perf/ui-performance#iden

[2]  performance,
reproduce the activity in your app.
Then select the new frames in the frames chart
to inspect the timeline events
with the layers disabled.
If raster time has significantly decreased,
excessive use of the effects you disabled might be contributing
to the jank you saw in your app.

**Render Clip layers**
: Disable this option to check whether excessive use of clipping
  is affecting performance.
  If performance improves with this option disabled,
  try to reduce the use of clipping effects in your app.

**Render Opacity layers**
:  Disable this option to check whether
   excessive use of opacity effects are affecting performance.
   If performance improves with this option disabled,
   try to reduce the use of opacity effects in your app.

**Render Physical Shape layers**
: Disable this option to check whether excessive
  use of physical modeling effects are affecting performance,
  such as shadows or elevation.
  If performance improves with this option disabled,
  try t

[3]  in your tree,
  check the **Inspector Settings** dialog to ensure that your package
  directories are properly configured -
  [#4306](https://github.com/flutter/devtools/pull/4306)

  ![frame_analysis](/assets/images/docs/tools/devtools/release-notes/images-2.17.0/package_directories.png "package directories")

## Performance updates

* Added a **Frame Analysis** tab to the Performance page.
  When analyzing a janky Flutter frame,
  this view provides hints for how to diagnose the jank and
  detects expensive operations that might have
  contributed to the slow frame time.
  This view also shows a breakdown of your Flutter frame time
  per phase (**Build**, **Layout**, **Paint**, and **Raster**)
  to try to guide you in the right direction -
  [#4339](https://github.com/flutter/devtools/pull/4339)

  ![frame_analysis](/assets/images/docs/tools/devtools/release-notes/images-2.17.0/frame_analysis.png "frame analysis")

## Full commit history

To find a complete list of changes since the

[4] er resources

To learn how to monitor an app's performance and
detect jank using DevTools, check out a guided
[Performance View tutorial][performance-tutorial].

[GPU graph]: /perf/ui-performance#identifying-problems-in-the-gpu-graph
[Flutter performance profiling]: /perf/ui-performance
[Reduce shader compilation jank on mobile]: /perf/rendering-performance
[Import and export]: #import-and-export
[performance-tutorial]: https://medium.com/@fluttergems/mastering-dart-flutter-devtools-performance-view-part-8-of-8-4ae762f91230
[track-widgets]: /_EYk-E29edo?t=623
[track-layouts]: /_EYk-E29edo?t=676
[track-paints]: /_EYk-E29edo?t=748

[5] r Flutter
app. Frames that perform shader compilation are marked in dark
red:

![Screenshot of shader compilation for a frame](/assets/images/docs/tools/devtools/shader-compilation-frames-chart.png)

For more information on how to reduce shader compilation jank,
check out [Reduce shader compilation jank on mobile][].

## Frame analysis tab

Selecting a janky frame (slow, colored in red)
from the Flutter frames chart above shows debugging hints
in the Frame analysis tab. These hints help you diagnose
jank in your app, and notify you of any expensive operations
that we have detected that might have contributed to the slow frame time.

![Screenshot of the frame analysis tab](/assets/images/docs/tools/devtools/frame-analysis-tab.png)

## Timeline events tab

The timeline events chart shows all event tracing from your application.
The Flutter framework emits timeline events as it works to build frames,
draw scenes, and track other activity such as HTTP request timings
and garbage collection

---
## 13. (id: q014)

**Soru:** What are the steps for generating type-safe platform bindings with Pigeon?

**Referans cevap:** Create the Pigeon definition file in Dart (with @HostApi/@FlutterApi annotations), run the generator, implement the generated native interface on each platform, then call the API from Flutter.

**Sistemin cevabı:** To generate type‑safe platform bindings with Pigeon, first create a Pigeon definition file in Dart (usually outside the lib directory, e.g., pigeons/messages.dart) that defines data structures and APIs using @HostApi and @FlutterApi. Then run the Pigeon generator tool to produce the corresponding Dart and native code. Next, implement the generated host interface on each target platform. Finally, call the generated API from your Flutter code.

**Modele verilen pasajlar:**

[1] wing:

- You need desktop support on Windows or Linux.
- You want zero external toolchains.

## Developer flow

Generate type-safe bindings with Pigeon using the following steps:

1.  Create the Pigeon definition file.
1.  Generate the code.
1.  Implement the native interface.
1.  Call the API from Flutter.

To start, create a Pigeon definition file in Dart
(typically outside of your `lib/` directory, such as `pigeons/messages.dart`).
This file defines the data structures and the API interfaces
using Pigeon annotations like `@HostApi` and `@FlutterApi`.
Next, run the Pigeon generator tool, which parses your Pigeon definition file
and produces the necessary code for both Dart and your target native platform.

If you're using Pigeon with the native interop communication option,
set `appDirectory`, `swiftOptions: SwiftOptions(useFfi: true, ffiModuleName: 'Runner')`,
and `kotlinOptions: KotlinOptions(useJni: true)` in the `@ConfigurePigeon`
section of your Pigeon definition file.
For compl

[2] ## Overview

[Pigeon][pigeon-pub] replaces the manual setup of raw platform channels
with generated, type-safe APIs.
This helps prevent typos in method names or mismatched argument types.

For low-level integrations that require direct access to native memory
or C and C++ libraries, use [FFIgen](/interop/ffigen)
or [JNIgen](/interop/jnigen) instead.

## Choose a communication option with Pigeon

Pigeon supports the following two communication options
depending on your target platform and performance needs:
native interop (direct FFI and JNI, in preview) or platform channels.

### Pigeon with native interop (preview) {:#pigeon-with-native-interop}

Pigeon with native interop is in preview and isn't
stable for production use.

Pigeon with native interop generates direct native bindings using
[FFIgen](/interop/ffigen) (FFI on iOS and macOS) and
[JNIgen](/interop/jnigen) (JNI on Android).

Try this preview option if your use case requires any of the following:

- You need synchronous execu

[3] egenerate the code, and then update your implementation accordingly.

## Examples

To explore a complete implementation of this flow,
including the Pigeon definition file, generated code,
and native implementations, refer to the following examples:

- [Example of Pigeon with native interop][pigeon-native-example]
- [Example of Pigeon with platform channels][pigeon-example]
- [`shared_preferences` plugin][shared-preferences-source]

## Constraints and limitations

Keep the following constraints and limitations in mind when working with Pigeon:

### High-frequency data

For specialized use cases requiring direct manipulation of raw native pointers
or C and C++ memory management,
use [FFIgen](/interop/ffigen) or
[JNIgen](/interop/jnigen) instead.

### Inheritance

Pigeon doesn't support complex inheritance.
Flatten your data models where possible.

### Async errors

If you use [Pigeon with platform channels](#pigeon-with-platform-channels),
`@async` methods generate Kotlin `suspend` and S

[4]  Dart API.
- [JNIgen](/interop/jnigen) inspects Java and Kotlin classes,
  JAR and AAR files, or Android SDK packages to generate direct JNI bindings.
  Wrapping an Android package with JNIgen produces an
  Android-shaped Dart API.

### Top-down with Pigeon

[Pigeon](/interop/pigeon) starts from a single Dart schema that
defines an intentional, platform-agnostic boundary contract once and
enforces identical types and signatures across Android, iOS, macOS,
Windows, and Linux.
You implement the generated host interface on each target platform
while Pigeon handles type safety, data conversion, and cross-runtime
memory safety across the boundary.

Pigeon generates bindings over
[platform channels](/platform-integration/platform-channels)
for all supported platforms, and offers a preview option to generate
direct native interop bindings using [FFIgen](/interop/ffigen)
on iOS and macOS and [JNIgen](/interop/jnigen) on Android.

## Package your interop code

Depending on how you plan to share

[5] geon/native_interop_guide.md
[pigeon-migration-guide]: /blob/main/packages/pigeon/native_interop_migration_guide.md
[shared-preferences-source]: /tree/main/packages/shared_preferences
[native-interop-demos]: /tree/main/native_interop_demos
[issue-195877]: /issues/195877
[pigeon-video]: ?v=GHH5DHmg_gE

---
## 14. (id: q048)

**Soru:** My app stutters while scrolling. How do I profile it and what general practices help?

**Referans cevap:** Profile in profile mode (not debug) with the DevTools Performance view to see UI and raster thread work per frame, and follow the performance best practices such as avoiding unnecessarily large rebuilds.

**Sistemin cevabı:** To profile scrolling jank, run an integration test that scrolls through a list while using the IntegrationTestWidgetsFlutterBinding’s traceAction method to record a performance timeline and save the results (see passages 1 and 3). In the running app you can enable the Performance Overlay to see frame‑time metrics and open the Performance View in DevTools for detailed charts (passage 2). Adding Dart tracing via the dart:developer package lets you pinpoint slow code sections in DevTools. These tools help you locate heavy rebuilds or expensive paint work so you can keep each frame under 16 ms for smooth scrolling.

**Modele verilen pasajlar:**

[1] When it comes to mobile apps, performance is critical to user experience.
Users expect apps to have smooth scrolling and meaningful animations free of
stuttering or skipped frames, known as "jank." How to ensure that your app
is free of jank on a wide variety of devices?

There are two options: first, manually test the app on different devices.
While that approach might work for a smaller app, it becomes more
cumbersome as an app grows in size. Alternatively, run an integration
test that performs a specific task and records a performance timeline.
Then, examine the results to determine whether a specific section of
the app needs to be improved.

In this recipe, learn how to write a test that records a performance
timeline while performing a specific task and saves a summary of the
results to a local file.

Recording performance timelines isn't supported on web.
For performance profiling on web, see
[Debugging performance for web apps][]

This recipe uses the following steps:

  1. Writ

[2] ## Overview

App performance encompasses various aspects, from raw speed and I/O throughput
to the smoothness of the user interface. While this page primarily focuses on UI
smoothness (lack of stutter or jank), the tools described here can often be used
to diagnose other performance issues as well.

Flutter offers several tools for performance analysis. Here are a few of them:

* **The Performance Overlay**: Displays a simplified set of metrics directly
  within your running app. To learn more, see the sections in this topic.

* **The Performance View**: A web-based interface that connects to your app and
  displays detailed performance metrics. Part of the DevTools utility. To learn
  more, see [Use the Performance View][].

* **Performance tracing within Dart**: Add tracing directly into your app's
  Dart code, using the `dart:developer package`, and then track your app's
  performance in the DevTools utility. To learn more, see [Tracing Dart code][].

* **Benchmarking**: You can mea

[3] to a local file.

Recording performance timelines isn't supported on web.
For performance profiling on web, see
[Debugging performance for web apps][]

This recipe uses the following steps:

  1. Write a test that scrolls through a list of items.
  2. Record the performance of the app.
  3. Save the results to disk.
  4. Run the test.
  5. Review the results.

## 1. Write a test that scrolls through a list of items

In this recipe, record the performance of an app as it scrolls through a
list of items. To focus on performance profiling, this recipe builds
on the [Scrolling][] recipe in widget tests.

Follow the instructions in that recipe to create an app and write a test to
verify that everything works as expected.

## 2. Record the performance of the app

Next, record the performance of the app as it scrolls through the
list. Perform this task using the [`traceAction()`][]
method provided by the [`IntegrationTestWidgetsFlutterBinding`][] class.

This method runs the provided function

[4] Scrollbars

On **Material-based platforms** (such as Android and web),
scrollbars are typically visible during scrolling
and may remain visible depending on the platform and theme.

On **Cupertino-based platforms** (such as iOS),
scrollbars are more minimal and generally only appear briefly
while the user is actively scrolling, fading out when interaction stops.

This difference reflects each platform’s visual conventions
and helps maintain a native look and feel across devices.

### Momentum

On **iOS**,
repeated flings in the same direction stacks momentum
and builds more speed with each successive fling.
There is no equivalent behavior on Android.

<div class="wrapping-row">
  <DashImage figure image="platform-adaptations/scroll-momentum-ios.webp" caption="iOS scroll momentum" alt="Repeated scroll flings building momentum on iOS" />
</div>

### Return to top

On **iOS**,
tapping the OS status bar scrolls the primary
scroll controller to the top position.
There is no equivalent behav

[5] A so big?

App bundle size includes the Flutter engine, framework code,
application logic, and bundled assets (such as images, fonts, and audio).
Always create a release build (`flutter build apk` or `flutter build appbundle`
for Android, and `flutter build ipa` for iOS),
which removes debug symbols and enables compiler optimizations.
To analyze and reduce app size, see [Measuring your app's size][].

### Is Flutter ABI compatible?

Flutter and Dart don't provide application binary interface (ABI)
compatibility across different compiler releases.
Always compile your application using matching SDK versions.

### How does Flutter handle scrolling?

Flutter provides platform-specific scroll physics
that match the native scrolling behavior of each platform
(such as momentum scrolling on iOS and overscroll stretch on Android).
For more details, see the [scrolling][] documentation.

[scrolling]: /ui/layout/scrolling

## Framework

### Why is the build() method on State, rather than StatefulW

---
## 15. (id: q021)

**Soru:** How does a user type a line break in the AI chat prompt box on a phone versus a desktop?

**Referans cevap:** On mobile, tap the Return key on the virtual keyboard; on web and desktop, press Shift+Enter.

**Sistemin cevabı:** On a mobile device, the user creates a line break by tapping the Return key on the virtual keyboard. On a desktop (or web) computer, the user creates a line break by pressing Shift + Enter. This lets the user embed newlines without submitting the prompt.

**Modele verilen pasajlar:**

[1] t manually as they enter it,
they can do so. The gesture for that activity differs based on the platform
they're using:

* **Mobile**: Tap Return key on the virtual keyboard
* **Web**: Press `Shift+Enter`
* **Desktop**: Press `Shift+Enter`

These options look like the following:

**Web and Desktop**:

![Screenshot of entering text on
desktop](/assets/images/docs/ai-toolkit/desktop-enter-text.png)

**Mobile**:

![Screenshot of entering text on
mobile](/assets/images/docs/ai-toolkit/mobile-enter-text.png)

## Voice input

In addition to text input the chat view can take an audio recording as input by
tapping the Mic button, which is visible when no text has yet been entered.

Tap the **Mic** button to start the recording:

![Screenshot of entering
text](/assets/images/docs/ai-toolkit/enter-textfield.png)

Select the **Stop** button to translate the user's voice input into text:

This text can then be edited, augmented and submitted as normal.

![Screenshot of entered
voice](/assets/image

[2]  the most recent message for
  resubmission to the LLM.
* **Material and Cupertino**: Adapts to the best practices of both design
  languages.

[`LlmChatView`]:
    /flutter_ai_toolkit/latest/flutter_ai_toolkit/LlmChatView-class.html

## Multiline text input

The user has  options when it comes to submitting their prompt once they've
finished composing it, which again differs depending on their platform:

* **Mobile**: Tap the **Submit** button
* **Web**: Press **Enter** or tap the **Submit** button
* **Desktop**: Press **Enter** or tap the **Submit** button

In addition, the chat view supports text prompts with embedded newlines in them.
If the user has existing text with newlines, they can paste them into the prompt
text field as normal.

If they'd like to embed newlines into their prompt manually as they enter it,
they can do so. The gesture for that activity differs based on the platform
they're using:

* **Mobile**: Tap Return key on the virtual keyboard
* **Web**: Press `Shift+En

[3] he initial prompt and response is used to ask the LLM what an
appropriate title should be. In fact, the titles of the chats in the screenshots
in this page were set automatically.

To build and run the sample, follow the instructions in the [AI Chat README][].

[AI Chat README]: https://github.com/csells/flutter_ai_chat

[4] r can long-tap a prompt or response and choose the
Copy option:

![Long tap to see the copy
button](/assets/images/docs/ai-toolkit/long-tap-choose-copy.png)

## Message editing

If the user would like to edit their last prompt and cause the LLM to take
another run at it, they can do so. On the desktop, the user can tap the **Edit**
button alongside the **Copy** button for their most recent prompt:

![How to edit prompt](/assets/images/docs/ai-toolkit/how-to-edit-prompt.png)

On a mobile device, the user can long-tap and get access to the **Edit** option
on their most recent prompt:

![How to access edit
menu](/assets/images/docs/ai-toolkit/accessing-edit-menu.png)

Once the user taps the **Edit** button, they enter Editing mode, which removes
both the user's last prompt and the LLM's last response from the chat history,
puts the text of the prompt into the text field, and provides an Editing
indicator:

![How to exit editing
mode](/assets/images/docs/ai-toolkit/how-to-exit-editing-mode

[5] response from the chat history,
puts the text of the prompt into the text field, and provides an Editing
indicator:

![How to exit editing
mode](/assets/images/docs/ai-toolkit/how-to-exit-editing-mode.png)

In Editing mode, the user can edit the prompt as they choose and submit it to
have the LLM produce a response as normal. Or, if they change their mind, they
can tap the **X** near the Editing indicator to cancel their edit and restore
their previous LLM response.

## Material and Cupertino

When the `LlmChatView` widget is hosted in a [Material app][], it uses
facilities provided by the Material design language, such as Material's
[`TextField`][]. Likewise, when hosted in a [Cupertino app][], it uses those
facilities, such as [`CupertinoTextField`][].

![Cupertino example app](/assets/images/docs/ai-toolkit/cupertino-chat-app.png)

However, while the chat view supports both the Material and Cupertino app types,
it doesn't automatically adopt the associated themes. Instead, that's se

---
## 16. (id: q071)

**Soru:** Uygulamamda Android'in tahmini geri (predictive back) animasyonunu nasıl açarım?

**Referans cevap:** In android/app/src/main/AndroidManifest.xml, add android:enableOnBackInvokedCallback="true" to the <application> tag (requires Android 13 or later).

**Sistemin cevabı:** AndroidManifest.xml dosyasını açıp `<application>` etiketine `android:enableOnBackInvokedCallback="true"` özniteliğini ekleyin. Bu ayar Android 13 ve üzerindeki cihazlarda tahmini geri (predictive back) animasyonunu etkinleştirir; Android 14'te ise zaten varsayılan olarak açıktır.
```xml
<application
    android:label="my_app"
    android:name="${applicationName}"
    android:icon="@mipmap/ic_launcher"
    android:enableOnBackInvokedCallback="true">
    <!-- ... -->
</application>
```

**Modele verilen pasajlar:**

[1] The Android predictive back gesture lets users preview
where a back gesture will navigate to,
whether that's the previous screen or the home screen,
before they commit to or cancel it.

## Overview

Starting with Android 14 (API level 34),
predictive back animations are enabled by default for system gestures
when supported by the application.
Flutter provides built-in support for predictive back animations across
default page route transitions and custom pop handling.

## Enable predictive back in Android

To support predictive back gestures in your Flutter app
on Android 13 or later:

1. Open `android/app/src/main/AndroidManifest.xml`.
1. Add `android:enableOnBackInvokedCallback="true"` to the `<application>` tag:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="my_app"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:enableOnBackInvokedCallback="true">
        <!--

[2] ">
    <application
        android:label="my_app"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:enableOnBackInvokedCallback="true">
        <!-- ... -->
    </application>
</manifest>
```

## Handle back gestures with PopScope

To customize back navigation or prevent users
from accidentally leaving a screen,
use the [`PopScope`][] widget.
`PopScope` replaces the deprecated `WillPopScope` widget
and supports predictive back gestures.

### Callback parameters

`PopScope` uses the `onPopInvokedWithResult` callback:

* `didPop`: A boolean indicating whether the pop operation succeeded.
  If `canPop` is `false`, `didPop` is `false`.
* `result`: An optional return payload passed when popping the route
  (for example, with `Navigator.pop(context, result)`).

### Example: Intercepting back navigation

```dart
PopScope(
  canPop: false,
  onPopInvokedWithResult: (bool didPop, Object? result) async {
    if (didPop) {
      return;
    }
  

[3] /div>
    <div class="card-content">
      <p>Learn how to add the predictive back gesture to your app on Android.</p>
    </div>
  </a>
  <a class="card outlined-card" href="/platform-integration/android/call-jetpack-apis">
    <div class="card-header">
      <span class="card-title">Call JetPack APIs</span>
    </div>
    <div class="card-content">
      <p>Learn how the latest Android APIs in your app from Dart.</p>
    </div>
  </a>
  <a class="card outlined-card" href="/interop/bind-native-code">
    <div class="card-header">
      <span class="card-title">Bind to native code</span>
    </div>
    <div class="card-content">
      <p>Learn how to bind to native code from your app on Android.</p>
    </div>
  </a>
  <a class="card outlined-card" href="/platform-integration/android/platform-views">
    <div class="card-header">
      <span class="card-title">Embed an Android view</span>
    </div>
    <div class="card-content">
      <p>Learn how to host native Android views in your 

[4]            }
            }
        }
    }
    ```

These steps show how to launch a native Android activity from a Flutter app,
which can sometimes be an easy way to connect to specific Android functionality.

[5] text, result)`).

### Example: Intercepting back navigation

```dart
PopScope(
  canPop: false,
  onPopInvokedWithResult: (bool didPop, Object? result) async {
    if (didPop) {
      return;
    }
    final shouldLeave = await _showExitConfirmationDialog(context);
    if (shouldLeave && context.mounted) {
      Navigator.of(context).pop(result);
    }
  },
  child: Scaffold(
    appBar: AppBar(title: const Text('Form Screen')),
    body: const Center(child: Text('Complete the form before leaving.')),
  ),
)
```

## More information

For more details on API migrations,
see the [Android predictive back migration guide][].

[`PopScope`]: /flutter/widgets/PopScope-class.html
[Android predictive back migration guide]: /release/breaking-changes/android-predictive-back

---
## 17. (id: q005)

**Soru:** Can Dart code keep running when my app isn't in the foreground, and how is that set up?

**Referans cevap:** Yes. Set up an isolate for background execution using callbacks and a callback dispatcher; the WorkManager plugin adds persistent background tasks that survive app restarts and reboots.

**Sistemin cevabı:** Yes, Dart code can keep running when the app is not in the foreground. In Flutter you set this up by creating a background isolate, usually via a callback dispatcher that the OS can invoke, and you can use the WorkManager plugin to schedule persistent background tasks that survive app restarts and reboots. The isolate is registered with the plugin and the Dart callback is executed even when the app is backgrounded. This allows your Dart code to continue executing without the main UI isolate being active.

**Modele verilen pasajlar:**

[1] cution of Dart code, see the Flutter blog post by Ben Konyi,
[Executing Dart in the Background with Flutter Plugins and
Geofencing][background-processes].  At the end of this article,
you'll find links to example code, and relevant documentation for Dart,
iOS, and Android.

[background-processes]: /executing-dart-in-the-background-with-flutter-plugins-and-geofencing
[WorkManager]: /workmanager

[2] Have you ever wanted to execute Dart code in the
background—even if your app wasn't the currently active app?
Perhaps you wanted to implement a process that watches the time,
or that catches camera movement.
In Flutter, you can execute Dart code in the background.

The mechanism for this feature involves setting up an isolate.
_Isolates_ are Dart's model for multithreading,
though an isolate differs from a conventional thread
in that it doesn't share memory with the main program.
You'll set up your isolate for background execution using
callbacks and a callback dispatcher.

Additionally, the [WorkManager] plugin enables persistent background processing
that keeps tasks scheduled through app restarts and system reboots.

For more information and a geofencing example that uses background
execution of Dart code, see the Flutter blog post by Ben Konyi,
[Executing Dart in the Background with Flutter Plugins and
Geofencing][background-processes].  At the end of this article,
you'll find link

[3] code during runtime.

A single Dart runtime exists per application session on
Android and iOS.

A one-time Dart VM start is done when constructing the
[`FlutterEngine`][android-engine] for the first time on
**Android** and when [running a Dart entrypoint][ios-engine]
for the first time on **iOS**.

At this point, your Dart code's [snapshot][]
is also loaded into memory from your application's files.

This is a generic process that also occurs if you used the
[Dart SDK][] directly, without the Flutter engine.

The Dart VM never shuts down after it's started.

### Creating and running a Dart Isolate

After the Dart runtime is initialized,
the Flutter engine's usage of the Dart
runtime is the next step.

This is done by starting a [Dart `Isolate`][] in the Dart runtime.
The isolate is Dart's container for memory and threads.
A number of [auxiliary threads][] on the host platform are
also created at this point to support the isolate, such
as a thread for offloading GPU handling and another

[4] When a user runs a mobile app and then selects another
app to run, the first app is moved to the background,
or _backgrounded_. The operating system (both iOS and Android)
might kill the backgrounded app to release memory and
improve performance for the app running in the foreground.

When the user selects the app again, bringing it
back to the foreground, the OS relaunches it.
But, unless you've set up a way to save the
state of the app before it was killed,
you've lost the state and the app starts from scratch.
The user has lost the continuity they expect,
which is clearly not ideal.
(Imagine filling out a lengthy form and being interrupted
by a phone call _before_ clicking **Submit**.)

So, how can you restore the state of the app so that
it looks like it did before it was sent to the
background?

Flutter has a solution for this with the
[`RestorationManager`][] (and related classes)
in the [services][] library.
With the `RestorationManager`, the Flutter framework
provides the state

[5] ding screen readers (TalkBack, VoiceOver), large text scaling,
high-contrast themes, and hardware switch access.
For details, see [Accessibility][accessibility documentation].

[accessibility documentation]: /ui/accessibility

### How do I write parallel and/or concurrent apps for Flutter?

Dart uses an event loop for asynchronous operations (`Future` and `Stream`).
For CPU-intensive tasks, Flutter supports isolates—isolated execution
threads with independent memory heaps that communicate through message passing.
You can use [`Isolate.run()`][] or the [`compute()`][] function
to run heavy computations in the background.

[`Isolate.run()`]: /flutter/dart-isolate/Isolate/run.html
[`compute()`]: /flutter/foundation/compute.html

### Can I run Dart code in the background of a Flutter app?

Yes. You can execute Dart code in background processes on Android and iOS
using background execution packages and platform service integrations.

### Can I use JSON, XML, or Protocol Buffers with Flutter

---
## 18. (id: q034)

**Soru:** How do I make a list scroll sideways instead of vertically?

**Referans cevap:** Set scrollDirection: Axis.horizontal on the ListView.

**Sistemin cevabı:** Use a ListView and set its scrollDirection to Axis.horizontal, which changes the default vertical scrolling to horizontal. This makes the list scroll sideways and you can provide children as usual. Example:
```dart
ListView(
  scrollDirection: Axis.horizontal,
  children: [
    for (final color in Colors.primaries)
      Container(width: 160, color: color),
  ],
),
```

**Modele verilen pasajlar:**

[1]   child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                for (final color in Colors.primaries)
                  Container(width: 160, color: color),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

<noscript>
  <img src="/assets/images/docs/cookbook/horizontal-list.webp" alt="Horizontal List Demo" class="site-mobile-screenshot" />
</noscript>

[2] You might want to create a list that scrolls
horizontally rather than vertically.
The [`ListView`][] widget supports horizontal lists.

Use the standard `ListView` constructor, passing in a horizontal
`scrollDirection`, which overrides the default vertical direction.

```dart highlightLines=2
ListView(
  scrollDirection: Axis.horizontal,
  children: [
    for (final color in Colors.primaries)
      Container(width: 160, color: color),
  ],
),
```

[`ListView`]: /flutter/widgets/ListView-class.html

## Interactive example

```dartpad title="Flutter horizontal list hands-on example in DartPad" run="true"
import 'dart:ui';

// DartPad doesn't support `material_ui` yet,
// so this example imports Material from the Flutter SDK.
// To run locally, depend on `material_ui` and use this import instead:
// import 'package:material_ui/material_ui.dart';
import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

[3] ren to have the given extent in the scroll direction.
||scroll Direction|[ [`Axis`][] ] The axis along which the scroll view scrolls.
||                                                                                                            |                                                                                                                                        |
| [`FlatList`](https://reactnative.dev/docs/flatlist)                    | [`ListView.builder`][]               | The constructor for a linear array of widgets that are created on demand.
||itemBuilder [required] |[[`IndexedWidgetBuilder`][]] helps in building the children on demand. This callback is called only with indices greater than or equal to zero and less than the itemCount.
||itemCount |[ int ] improves the ability of the `ListView` to estimate the maximum scroll extent.
|                                                                                           |                                       

[4] Perhaps you want to create a list where all list items
are spaced evenly, so that the items take up the visible space.
For example, the four items in the following image are spaced evenly,
with "Item 0" at the top, and "Item 3" at the bottom.

![Spaced items](/assets/images/docs/cookbook/spaced-items-1.png){:.site-mobile-screenshot}

At the same time, you might want to allow users
to scroll through the list when the list of items won't fit,
maybe because a device is too small, a user resized a window,
or the number of items exceeds the screen size.

![Scrollable items](/assets/images/docs/cookbook/spaced-items-2.png){:.site-mobile-screenshot}

Typically, you use [`Spacer`][] to tune the spacing between widgets,
or [`Expanded`][] to expand a widget to fill the available space.
However, these solutions are not possible inside scrollable widgets,
because they need a finite height constraint.

This recipe demonstrates how to use [`LayoutBuilder`][] and [`ConstrainedBox`][]
to space out lis

[5] .
          // If you change the scrollDirection to horizontal,
          // this produces 2 rows.
          crossAxisCount: 2,
          // Generate 100 widgets that display their index in the list.
          children: List.generate(100, (index) {
            return Center(
              child: Text(
                'Item $index',
                style: TextTheme.of(context).headlineSmall,
              ),
            );
          }),
        ),
      ),
    );
  }
}
```

<noscript>
  <img src="/assets/images/docs/cookbook/grid-list.webp" alt="Grid List Demo" class="site-mobile-screenshot" />
</noscript>

[`GridView`]: /flutter/widgets/GridView-class.html
[`GridView.count()`]: /flutter/widgets/GridView/GridView.count.html

---
## 19. (id: q022)

**Soru:** How do I keep my Play Store service account credentials safe when building on a CI server?

**Referans cevap:** Don't leave credentials on the ephemeral server; store them in the CI system's encrypted environment variables and pass them to the build with --dart-define, taking care not to echo them to the console.

**Sistemin cevabı:** Store the Play Store service account JSON in an encrypted environment variable on your CI system (you can base64‑encode it if needed) and read it at build time, for example using `ENV['PLAY_STORE_UPLOAD_KEY']` in your Fastfile. Pass the credential to `upload_to_play_store` via the `json_key_data` parameter. Ensure the variable is never echoed to the console and that it is not exposed in pull‑request builds. This keeps the key secret while allowing automated uploads.

**Modele verilen pasajlar:**

[1] ncrypted variable.
          Read the environment variable directly in your `Fastfile`.
          ```plaintext
          upload_to_play_store(
            ...
            json_key_data: ENV['<variable name>']
          )
          ```
        * Serialize your upload key (for example, using base64) and save it as
          an encrypted environment variable. You can deserialize it on your CI
          system during the install phase with
          ```bash
          echo "$PLAY_STORE_UPLOAD_KEY" | base64 --decode > [path to your upload keystore]
          ```
    * ![iOS](/assets/images/docs/cd/ios.png) On iOS:
        * Move the local environment variable `FASTLANE_PASSWORD` to use
          encrypted environment variables on the CI system.
        * The CI system needs access to your distribution certificate.
          fastlane's [Match][] system is
          recommended to synchronize your certificates across machines.

2. It's recommended to use a Gemfile instead of using an indetermi

[2] us Integration (CI) systems generally support encrypted environment
variables to store private data. You can pass these environment variables
using `--dart-define MY_VAR=MY_VALUE` while building the app.

**Take precaution not to re-echo those variable values back onto the console in
your test scripts**. Those variables are also not available in pull requests
until they're merged to ensure that malicious actors cannot create a pull
request that prints these secrets out. Be careful with interactions with these
secrets in pull requests that you accept and merge.

1. Make login credentials ephemeral.
    * ![Android](/assets/images/docs/cd/android.png) On Android:
        * Remove the `json_key_file` field from `Appfile` and store the string
          content of the JSON in your CI system's encrypted variable.
          Read the environment variable directly in your `Fastfile`.
          ```plaintext
          upload_to_play_store(
            ...
            json_key_data: ENV['<variable

[3] >
<li>

As mentioned earlier, don't forget to set your login keychain
as the default to avoid authentication issues
with apps on your machine:

```bash
keychain use-login
```

</li>
</ol>

## Release your app on TestFlight

[TestFlight][] allows developers to push their apps
to internal and external testers. This optional step
covers releasing your build on TestFlight.

1. Navigate to the TestFlight tab of your app's application
   details page on [App Store Connect][appstoreconnect_login].
1. Select **Internal Testing** in the sidebar.
1. Select the build to publish to testers, then click **Save**.
1. Add the email addresses of any internal testers.
   You can add additional internal users in the **Users and Roles**
   page of App Store Connect,
   available from the dropdown menu at the top of the page.

## Distribute to registered devices

See [distribution guide][distributionguide_macos]
to prepare an archive for distribution to designated Mac computers.

## Release your app to the

[4] th a digital certificate.

Android uses two signing keys: _upload_ and _app signing_.

* Developers upload an `.aab` or `.apk` file signed with
  an _upload key_ to the Play Store.
* The end-users download the `.apk` file signed with an _app signing key_.

To create your app signing key, use Play App Signing
as described in the [official Play Store documentation][].

To sign your app, use the following instructions.

[official Play Store documentation]: https://support.google.com/googleplay/android-developer/answer/7384423?hl=en

### Create an upload keystore

If you have an existing keystore, skip to the next step.
If not, create one using one of the following methods:

1. Follow the [Android Studio key generation steps][as-key-steps].
1. Run the following command at the command line:

   On macOS or Linux, use the following command:

   ```console
   keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA \
           -storetype JKS -keysize 2048 -validity 10000 -alias upload


[5] >
<li>

As mentioned earlier, don't forget to set your login keychain
as the default to avoid authentication issues
with apps on your machine:

```bash
keychain use-login
```

</li>
</ol>

You should receive an email within 30 minutes notifying you that
your build has been validated and is available to release to testers
on TestFlight. At this point you can choose whether to release
on TestFlight, or go ahead and release your app to the App Store.

## Release your app on TestFlight

[TestFlight][] allows developers to push their apps
to internal and external testers. This optional step
covers releasing your build on TestFlight.

1. Navigate to the TestFlight tab of your app's application
   details page on [App Store Connect][appstoreconnect_login].
1. Select **Internal Testing** in the sidebar.
1. Select the build to publish to testers, then click **Save**.
1. Add the email addresses of any internal testers.
   You can add additional internal users in the **Users and Roles**
   page o

---
## 20. (id: q024)

**Soru:** How do I feed audio data into a stream while using flutter_soloud?

**Referans cevap:** Create a buffer stream with SoLoud.instance.setBufferStream, play it, call SoLoud.instance.addAudioDataStream(stream, audioChunk) as data arrives, and mark the end with setDataIsEnded.

**Sistemin cevabı:** First create a buffer stream with SoLoud.instance.setBufferStream, then start playback using SoLoud.instance.play(stream). As your app receives audio chunks, feed them into the stream by calling SoLoud.instance.addAudioDataStream(stream, audioChunk) where audioChunk is a Uint8List containing the PCM data. When all data has been sent, mark the stream as finished with SoLoud.instance.setDataIsEnded(stream).

**Modele verilen pasajlar:**

[1] uffer stream:

```dart
final stream = SoLoud.instance.setBufferStream(
  bufferingType: BufferingType.released,
  sampleRate: 24000,
  channels: Channels.mono,
  format: BufferType.s16le, // pcm16bits
);
```

Play the stream:

```dart
final handle = await SoLoud.instance.play(stream);
```

As your app receives audio data, add it to the stream:

```dart
// TODO: Replace with your actual audio data.
final audioChunk = Uint8List.fromList([]);

SoLoud.instance.addAudioDataStream(
  stream,
  audioChunk,
);
```

When you're done with the audio stream, mark it as complete:

```dart
SoLoud.instance.setDataIsEnded(stream);
```

## More information

For more detailed information and examples,
visit the [`flutter_soloud` package][] on pub.dev or
check out the `flutter_soloud` Package of the Week video.

<div class="video-wrapper">
  <YouTubeEmbed id="2t6Bt04EyLw" title="flutter_soloud - Package of the Week"></YouTubeEmbed>
</div>

[2] ud.instance.init(
  sampleRate: 44100,
  bufferSize: 2048,
  channels: Channels.stereo,
);
```

## 3. Load audio

The `flutter_soloud` package supports various audio formats
including MP3, WAV, OGG, and FLAC.
You can load audio from different sources.

From a local file:

```dart
final sound = await SoLoud.instance.loadFile('path/to/sound.mp3');
```

From an app asset:

```dart
final sound = await SoLoud.instance.loadAsset('assets/sound.mp3');
```

From a network URL:

```dart
final sound = await SoLoud.instance.loadUrl(
  'https://example.com/sound.mp3',
  mode: LoadMode.memory,
);
```

From bytes in memory:

```dart
// TODO: Replace with your actual audio data.
final soundBytes = Uint8List.fromList([]);

final sound = await SoLoud.instance.loadMem(
  'reference_name.mp3',
  soundBytes,
  mode: LoadMode.memory,
);
```

## 4. Play audio

Once the audio is loaded,
you can play it using `SoLoud.instance.play`.
You can also configure gapless looping.

```dart
// Play the sound.
var handle

[3] This recipe demonstrates how to integrate the [`flutter_soloud` package][]
into your Flutter application to play sound effects and
background music with low latency.
To get started using the package, follow these steps:

[`flutter_soloud` package]: /flutter_soloud

## 1. Add the package dependency

To add `package:flutter_soloud` as a dependency, use `flutter pub add`:

```console
$ flutter pub add flutter_soloud
```

## 2. Initialize `SoLoud`

Before playing any audio,
you need to initialize the `SoLoud` instance.
You can also configure playback settings like sample rate,
buffer size, and the number of channels.

```dart
import 'package:flutter_soloud/flutter_soloud.dart';

// Initialize with default settings.
await SoLoud.instance.init();

// Or configure with custom settings.
await SoLoud.instance.init(
  sampleRate: 44100,
  bufferSize: 2048,
  channels: Channels.stereo,
);
```

## 3. Load audio

The `flutter_soloud` package supports various audio formats
including MP3, WAV, OGG, a

[4] andle, Duration(seconds: 5));
```

Set playback speed:

```dart
// Play twice as fast.
SoLoud.instance.setRelativePlaySpeed(handle, 2.0);
```

Adjust playback volume:

```dart
// Set playback to 50% volume.
SoLoud.instance.setVolume(handle, 0.5);
```

Fade the audio volume:

```dart
SoLoud.instance.fadeVolume(
  handle,
  0.0, // The volume to fade to.
  Duration(seconds: 2), // The duration of the fade.
);
```

Stop playback:

```dart
await SoLoud.instance.stop(handle);
```

## 6. Dispose of sound sources

When you are finished with a sound source,
remember to dispose of it to free up resources.

```dart
await SoLoud.instance.disposeSource(sound);
```

## 7. [Optional] Stream audio

The `flutter_soloud` package also supports streaming
audio data in real time.

Initialize and configure a buffer stream:

```dart
final stream = SoLoud.instance.setBufferStream(
  bufferingType: BufferingType.released,
  sampleRate: 24000,
  channels: Channels.mono,
  format: BufferType.s16le, // pcm16bits

[5] This recipe demonstrates how to use the [`record` package][] to add
audio recording and streaming capabilities to your Flutter app.
To get started using the package, follow these steps:

[`record` package]: /record

## 1. Add the package dependency

To add `package:record` as a dependency, use `flutter pub add`:

```console
$ flutter pub add record
```

## 2. Initialize an `AudioRecorder`

Initialize an `AudioRecorder` object. This is the primary object
that controls the recording process.

```dart
import 'package:record/record.dart';

final recorder = AudioRecorder();
```

## 3. Request user permission

Before recording, you need to request user permission.
You might also need to add platform-specific permission configurations.
Refer to the [`record` package][] documentation for details.

```dart
final recorder = AudioRecorder();
if (await recorder.hasPermission()) {
  // Permission granted, proceed with recording.
} else {
  // Permission denied.
}
```

## 4. Create a recording confi
