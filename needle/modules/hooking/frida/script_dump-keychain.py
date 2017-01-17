from core.framework.module import FridaScript
import json

class Module(FridaScript):
    meta = {
        'name': 'Frida Script: Keychain Dumper',
        'author': 'Bernard Wagner (@MWRLabs)',
        'description': 'Retrieve all keychain items',
        'options': (

        ),
    }

    JS = '''\
if (ObjC.available) {
  var constants = {
    "ck":"kSecAttrAccessibleAfterFirstUnlock",
    "ak":"kSecAttrAccessibleWhenUnlocked",
    "cku":"kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly",
    "dk":"kSecAttrAccessibleAlways",
    "dku":"kSecAttrAccessibleAlwaysThisDeviceOnly",
    "akpu":"kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly",
    "aku":"kSecAttrAccessibleWhenUnlockedThisDeviceOnly",
    "ck":"kSecAttrAccessibleAfterFirstUnlock",
    "cku":"kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly",
    "dk":"kSecAttrAccessibleAlways",
    "akpu":"kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly",
    "ak":"kSecAttrAccessibleWhenUnlocked",
    "aku":"kSecAttrAccessibleWhenUnlockedThisDeviceOnly",
    "dku":"kSecAttrAccessibleAlwaysThisDeviceOnly",
    "cert":"kSecClassCertificate",
    "class":"kSecClass",
    "genp":"kSecClassGenericPassword",
    "idnt":"kSecClassIdentity",
    "inet":"kSecClassInternetPassword",
    "keys":"kSecClassKey",
  }

  var SecItemCopyMatching = new NativeFunction(ptr(Module.findExportByName("Security","SecItemCopyMatching")),'pointer',['pointer','pointer']);
  var NSJSONSerialization = ObjC.classes.NSJSONSerialization;

  var query = ObjC.classes.NSMutableDictionary.dictionary();
  query.addObject_forKey_(ObjC.classes.__NSCFBoolean.numberWithBool_(true),"r_Attributes");
  query.addObject_forKey_(ObjC.classes.__NSCFBoolean.numberWithBool_(true),"r_Ref");
  query.addObject_forKey_(ObjC.classes.__NSCFBoolean.numberWithBool_(true),"r_Data");
  query.addObject_forKey_("m_LimitAll","m_Limit");

  var secItemClasses = ["genp", "inet", "cert", "keys", "idnt"];
  var secItemClass;

  for (secItemClassIter in secItemClasses) {
    query.setObject_forKey_(secItemClasses[secItemClassIter],"class");
    var resultPtr = Memory.alloc(Process.pointerSize);
    Memory.writePointer(resultPtr, NULL);
    if (SecItemCopyMatching(query, resultPtr) == 0) {
        var result = new ObjC.Object(Memory.readPointer(resultPtr));
        for (var i = 0; i < result.count(); i++){
            var entry = result.objectAtIndex_(i);
            send(JSON.stringify({
                Data: ObjC.classes.NSString.stringWithUTF8String_(entry.objectForKey_("v_Data").bytes()).valueOf(),
                EntitlementGroup: entry.objectForKey_("agrp").valueOf(),
                Protection: constants[entry.objectForKey_("pdmn")].valueOf(),
                UserPresence: entry.objectForKey_("musr") ? "Yes" : "No",
                CreationTime: entry.objectForKey_("cdat").valueOf(),
                Account: entry.objectForKey_("acct").valueOf(),
                Service: entry.objectForKey_("svce").valueOf(),
                ModifiedTime: entry.objectForKey_("mdat").valueOf(),
                kSecClass: constants[secItemClasses[secItemClassIter]]
            }));
          }
        }
    }
} else {
    console.log("Objective-C Runtime is not available!");
}
        '''

    # ==================================================================================================================
    # RUN
    # ==================================================================================================================
    def module_run(self):
        # Run the payload
        try:
            self.results = []
            self.printer.info("Parsing payload")
            hook = self.JS
            script = self.session.create_script(hook)
            script.on('message', self.on_message)
            script.load()
        except Exception as e:
            self.printer.warning("Script terminated abruptly")
            print(e)

    def on_message(self, message, data):
        try:
            if message:
                self.results.append(json.loads(message["payload"]))
        except Exception as e:
            print(message)
            print(e)

    def module_post(self):
        for key in self.results:
            print(json.dumps(key, indent=4, sort_keys=True))
