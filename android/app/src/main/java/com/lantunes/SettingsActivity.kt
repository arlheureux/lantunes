package com.lantunes

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout

class SettingsActivity : AppCompatActivity() {

    companion object {
        const val PREFS_NAME = "lantunes_prefs"
        const val KEY_SERVER_URL = "server_url"
        const val KEY_LOCAL_URL = "local_url"
        const val KEY_REMOTE_URL = "remote_url"
        const val KEY_MODE = "server_mode"
        const val MODE_LOCAL = "local"
        const val MODE_REMOTE = "remote"
        const val EXTRA_SELECTED_MODE = "selected_mode"
        const val REQUEST_RELOAD = 1
    }

    private lateinit var modeSpinner: Spinner
    private lateinit var localUrlEditText: TextInputEditText
    private lateinit var localUrlInputLayout: TextInputLayout
    private lateinit var remoteUrlEditText: TextInputEditText
    private lateinit var remoteUrlInputLayout: TextInputLayout
    private lateinit var saveButton: Button
    private lateinit var cancelButton: Button
    private lateinit var reloadButton: Button

    private var currentMode = MODE_LOCAL

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        initViews()
        setupModeSpinner()
        loadSettings()
        setupClickListeners()
    }

    private fun initViews() {
        modeSpinner = findViewById(R.id.modeSpinner)
        localUrlEditText = findViewById(R.id.localUrlEditText)
        localUrlInputLayout = findViewById(R.id.localUrlInputLayout)
        remoteUrlEditText = findViewById(R.id.remoteUrlEditText)
        remoteUrlInputLayout = findViewById(R.id.remoteUrlInputLayout)
        saveButton = findViewById(R.id.saveButton)
        cancelButton = findViewById(R.id.cancelButton)
        reloadButton = findViewById(R.id.reloadButton)
    }

    private fun setupModeSpinner() {
        val modes = arrayOf("Local (http)", "Remote (https)")
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, modes)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        modeSpinner.adapter = adapter
    }

    private fun loadSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        
        val localUrl = prefs.getString(KEY_LOCAL_URL, "") ?: ""
        val remoteUrl = prefs.getString(KEY_REMOTE_URL, "") ?: ""
        currentMode = prefs.getString(KEY_MODE, MODE_LOCAL) ?: MODE_LOCAL

        localUrlEditText.setText(localUrl)
        remoteUrlEditText.setText(remoteUrl)

        modeSpinner.setSelection(if (currentMode == MODE_REMOTE) 1 else 0)
    }

    private fun setupClickListeners() {
        saveButton.setOnClickListener {
            saveSettings()
        }

        cancelButton.setOnClickListener {
            finish()
        }

        reloadButton.setOnClickListener {
            reloadWithSelectedMode()
        }
    }

    private fun reloadWithSelectedMode() {
        val localUrl = localUrlEditText.text?.toString()?.trim() ?: ""
        val remoteUrl = remoteUrlEditText.text?.toString()?.trim() ?: ""

        val selectedMode = if (modeSpinner.selectedItemPosition == 1) MODE_REMOTE else MODE_LOCAL
        val url = if (selectedMode == MODE_LOCAL) localUrl else remoteUrl

        if (url.isEmpty()) {
            Toast.makeText(this, "Please enter a " + selectedMode + " server URL first", Toast.LENGTH_SHORT).show()
            return
        }

        val formattedUrl = if (selectedMode == MODE_LOCAL) {
            if (localUrl.isNotEmpty()) formatUrl(localUrl, "http://") else ""
        } else {
            if (remoteUrl.isNotEmpty()) formatUrl(remoteUrl, "https://") else ""
        }

        val resultIntent = Intent()
        resultIntent.putExtra(EXTRA_SELECTED_MODE, selectedMode)
        setResult(RESULT_OK, resultIntent)
        finish()
    }

    private fun saveSettings() {
        val localUrl = localUrlEditText.text?.toString()?.trim() ?: ""
        val remoteUrl = remoteUrlEditText.text?.toString()?.trim() ?: ""

        var hasError = false

        // Validate and format local URL
        var formattedLocalUrl = localUrl
        if (localUrl.isNotEmpty()) {
            formattedLocalUrl = formatUrl(localUrl, "http://")
            if (!isValidUrl(formattedLocalUrl)) {
                localUrlInputLayout.error = getString(R.string.url_invalid)
                hasError = true
            }
        }

        // Validate and format remote URL
        var formattedRemoteUrl = remoteUrl
        if (remoteUrl.isNotEmpty()) {
            formattedRemoteUrl = formatUrl(remoteUrl, "https://")
            if (!isValidUrl(formattedRemoteUrl)) {
                remoteUrlInputLayout.error = getString(R.string.url_invalid)
                hasError = true
            }
        }

        if (hasError) return

        // Determine mode from selected spinner position
        val selectedMode = if (modeSpinner.selectedItemPosition == 1) MODE_REMOTE else MODE_LOCAL

        // Auto-detect mode based on URL if not manually set
        val finalMode = selectedMode

        // Save all settings
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(KEY_LOCAL_URL, formattedLocalUrl)
            .putString(KEY_REMOTE_URL, formattedRemoteUrl)
            .putString(KEY_MODE, finalMode)
            .putString(KEY_SERVER_URL, if (finalMode == MODE_LOCAL) formattedLocalUrl else formattedRemoteUrl)
            .apply()

        Toast.makeText(this, R.string.settings_saved, Toast.LENGTH_SHORT).show()

        // Return to main activity
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK
        startActivity(intent)
        finish()
    }

    private fun formatUrl(url: String, defaultProtocol: String): String {
        return if (!url.startsWith("http://") && !url.startsWith("https://")) {
            "$defaultProtocol$url"
        } else {
            url
        }
    }

    private fun isValidUrl(url: String): Boolean {
        return try {
            val uri = java.net.URI(url)
            uri.host != null && uri.host!!.isNotEmpty()
        } catch (e: Exception) {
            false
        }
    }
}