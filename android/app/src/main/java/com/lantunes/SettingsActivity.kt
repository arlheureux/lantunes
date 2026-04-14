package com.lantunes

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout

class SettingsActivity : AppCompatActivity() {

    companion object {
        const val PREFS_NAME = "lantunes_prefs"
        const val KEY_SERVER_URL = "server_url"
    }

    private lateinit var urlEditText: TextInputEditText
    private lateinit var urlInputLayout: TextInputLayout
    private lateinit var saveButton: Button
    private lateinit var cancelButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        initViews()
        loadCurrentUrl()
        setupClickListeners()
    }

    private fun initViews() {
        urlEditText = findViewById(R.id.urlEditText)
        urlInputLayout = findViewById(R.id.urlInputLayout)
        saveButton = findViewById(R.id.saveButton)
        cancelButton = findViewById(R.id.cancelButton)
    }

    private fun loadCurrentUrl() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val currentUrl = prefs.getString(KEY_SERVER_URL, "") ?: ""
        urlEditText.setText(currentUrl)
    }

    private fun setupClickListeners() {
        saveButton.setOnClickListener {
            saveUrl()
        }

        cancelButton.setOnClickListener {
            finish()
        }
    }

    private fun saveUrl() {
        val url = urlEditText.text?.toString()?.trim() ?: ""

        // Validate URL
        if (url.isEmpty()) {
            urlInputLayout.error = getString(R.string.url_required)
            return
        }

        // Add https:// if no protocol specified
        val formattedUrl = if (!url.startsWith("http://") && !url.startsWith("https://")) {
            "https://$url"
        } else {
            url
        }

        // Basic URL validation
        if (!isValidUrl(formattedUrl)) {
            urlInputLayout.error = getString(R.string.url_invalid)
            return
        }

        // Save URL
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_SERVER_URL, formattedUrl).apply()

        Toast.makeText(this, R.string.settings_saved, Toast.LENGTH_SHORT).show()

        // Return to main activity
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK
        startActivity(intent)
        finish()
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