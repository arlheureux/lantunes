package com.lantunes

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible

class MainActivity : AppCompatActivity() {

    companion object {
        const val PREFS_NAME = "lantunes_prefs"
        const val KEY_SERVER_URL = "server_url"
        const val KEY_FIRST_LAUNCH = "first_launch"
        const val EXTRA_SELECTED_MODE = "selected_mode"
        const val PERMISSION_REQUEST_CODE = 1001
    }

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var offlineOverlay: LinearLayout
    private lateinit var errorOverlay: LinearLayout
    private lateinit var retryButton: Button
    private lateinit var errorRetryButton: Button
    private lateinit var settingsButton: Button

    private var isPageLoaded = false

    override fun onCreate(savedInstanceState: Bundle?) {
        try {
            super.onCreate(savedInstanceState)
            setContentView(R.layout.activity_main)

            initViews()
            
            // Setup WebView in try-catch to prevent crash
            try {
                setupWebView()
            } catch (e: Exception) {
                // Continue even if WebView setup fails
            }
            
            setupClickListeners()
            setupBackNavigation()

            val url = getServerUrl()
            if (url.isEmpty()) {
                showServerUrlDialog()
            }
        } catch (e: Exception) {
            // Catch any crash
            e.printStackTrace()
        }
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        
        // Check if URL changed or needs to be loaded
        val url = getServerUrl()
        if (url.isNotEmpty() && !isPageLoaded) {
            loadUrl()
        }
    }

    private fun initViews() {
        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)
        offlineOverlay = findViewById(R.id.offlineOverlay)
        errorOverlay = findViewById(R.id.errorOverlay)
        retryButton = findViewById(R.id.retryButton)
        errorRetryButton = findViewById(R.id.errorRetryButton)
        settingsButton = findViewById(R.id.settingsButton)
    }

    private fun setupWebView() {
        webView.apply {
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                databaseEnabled = true
                loadWithOverviewMode = true
                useWideViewPort = true
                builtInZoomControls = false
                displayZoomControls = false
                setSupportZoom(false)
                cacheMode = android.webkit.WebSettings.LOAD_DEFAULT
                allowContentAccess = true
                allowFileAccess = true
            }

webViewClient = LanTunesWebViewClient()
            webChromeClient = LanTunesChromeClient()
            setupJavaScriptInterface()
        }
    }
    
    private fun setupJavaScriptInterface() {
        // JavaScript interface disabled for now - causes crash
        // try {
        //     webView.addJavascriptInterface(this, "LanTunesAndroid")
        // } catch (e: Exception) {
        //     // Ignore
        // }
    }
    
    private fun setupClickListeners() {
        retryButton.setOnClickListener { retryLoad() }
        errorRetryButton.setOnClickListener { retryLoad() }
        settingsButton.setOnClickListener { openSettings() }
    }

    private fun setupBackNavigation() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    private fun getServerUrl(): String {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_SERVER_URL, "") ?: ""
    }

    private fun showServerUrlDialog() {
        val editText = EditText(this).apply {
            hint = "http://192.168.1.100:8080"
            setTextColor(getColor(R.color.white))
            setHintTextColor(getColor(R.color.gray))
        }

        AlertDialog.Builder(this)
            .setTitle("Server URL")
            .setMessage("Enter your LanTunes server address")
            .setView(editText)
            .setPositiveButton("Save") { _, _ ->
                val url = editText.text.toString().trim()
                if (url.isNotEmpty()) {
                    val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                    prefs.edit().putString(KEY_SERVER_URL, url).apply()
                    loadUrl()
                }
            }
            .setNegativeButton("Cancel") { _, _ ->
                finish()
            }
            .setCancelable(false)
            .show()
    }

    

    private fun loadUrl() {
        val url = getServerUrl()
        if (url.isNotEmpty()) {
            // Always show webview, hide overlays first
            hideOverlays()
            webView.isVisible = true
            progressBar.isVisible = true
            
            webView.loadUrl(url)
            Toast.makeText(this, "Loading: $url", Toast.LENGTH_SHORT).show()
        } else {
            showServerUrlDialog()
        }
    }

    private fun retryLoad() {
        isPageLoaded = false
        if (!isNetworkAvailable()) {
            showOffline()
            return
        }
        hideOverlays()
        loadUrl()
    }

    private fun openSettings() {
        val intent = Intent(this, SettingsActivity::class.java)
        startActivityForResult(intent, 1)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1) {
            isPageLoaded = false
            loadUrl()
        }
    }

    private fun showLoading() {
        progressBar.isVisible = true
        webView.isVisible = false
    }

    private fun hideLoading() {
        progressBar.isVisible = false
        webView.isVisible = true
    }

    private fun showOffline() {
        hideLoading()
        webView.isVisible = false
        offlineOverlay.isVisible = true
        errorOverlay.isVisible = false
    }

    private fun showError(message: String) {
        hideLoading()
        webView.isVisible = false
        errorOverlay.isVisible = true
        offlineOverlay.isVisible = false
        Toast.makeText(this, "Error: $message", Toast.LENGTH_LONG).show()
    }

    private fun hideOverlays() {
        offlineOverlay.isVisible = false
        errorOverlay.isVisible = false
    }

    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
        // Keep service running when app in background
        PlaybackService.startService(this)
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }

    private inner class LanTunesWebViewClient : WebViewClient() {

        override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
            val url = request?.url?.toString() ?: return false
            return handleUrl(url)
        }

        private fun handleUrl(url: String): Boolean {
            return if (url.startsWith("http://") || url.startsWith("https://")) {
                false
            } else {
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                } catch (e: Exception) {
                    // Ignore
                }
                true
            }
        }

        override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
            super.onPageStarted(view, url, favicon)
            showLoading()
            isPageLoaded = false
            Toast.makeText(this@MainActivity, "Starting to load: $url", Toast.LENGTH_SHORT).show()
        }

        override fun onPageFinished(view: WebView?, url: String?) {
            super.onPageFinished(view, url)
            hideLoading()
            hideOverlays()
            isPageLoaded = true
            Toast.makeText(this@MainActivity, "Page loaded: $url", Toast.LENGTH_SHORT).show()
        }

        override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
            super.onReceivedError(view, request, error)
            
            if (request?.isForMainFrame == true) {
                val errorCode = error?.errorCode ?: -1
                val errorDescription = error?.description?.toString() ?: "Unknown error"
                
                Toast.makeText(this@MainActivity, "WebView error: $errorDescription (code: $errorCode)", Toast.LENGTH_LONG).show()
                showError(errorDescription)
            }
        }
    }

    private inner class LanTunesChromeClient : WebChromeClient() {
        override fun onProgressChanged(view: WebView?, newProgress: Int) {
            super.onProgressChanged(view, newProgress)
            if (newProgress == 100) {
                progressBar.isVisible = false
            }
        }
    }

    @JavascriptInterface
    fun getCurrentSsid(): String {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), PERMISSION_REQUEST_CODE)
            return ""
        }
        
        return try {
            val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val connectionInfo = wifiManager.connectionInfo
            if (connectionInfo != null) {
                val ssid = connectionInfo.ssid
                if (ssid != null && ssid != "<unknown ssid>") {
                    ssid.removeSurrounding("\"")
                } else {
                    ""
                }
            } else {
                ""
            }
        } catch (e: Exception) {
            ""
        }
    }

    @JavascriptInterface
    fun isOnWifi(): Boolean {
        val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            webView.evaluateJavascript("if (window.LanTunes) window.LanTunes.onPermissionGranted();", null)
        }
    }

    private fun setupMediaSession() {
        // Bluetooth controls temporarily disabled - needs proper MediaSession setup
    }
}