// Raupi-Zifferblatt (Watch Face Format) – wird von .github/workflows/watchface.yml gebaut
plugins { id("com.android.application") version "9.0.0" }

android {
    enableKotlin = false
    namespace = "de.sparxfuna.raupi.watchface"
    compileSdk = 33
    defaultConfig {
        applicationId = "de.sparxfuna.raupi.watchface"
        minSdk = 33
        targetSdk = 33
        versionCode = (System.getenv("WF_CODE") ?: "1").toInt()
        versionName = System.getenv("WF_NAME") ?: "1.0"
    }
    signingConfigs {
        create("rb") {
            storeFile = file("release.p12")
            storeType = "pkcs12"
            storePassword = System.getenv("RB_KS_PASS")
            keyAlias = "raupenbuch"
            keyPassword = System.getenv("RB_KS_PASS")
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = false
            signingConfig = if (file("release.p12").exists()) signingConfigs.getByName("rb") else signingConfigs.getByName("debug")
        }
    }
}
