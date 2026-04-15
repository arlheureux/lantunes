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
        const val KEY_DEVICE_NAME = "device_name"
        const val KEY_MUSIC_PATH = "music_path"
    }

    private lateinit var deviceNameEditText: TextInputEditText
    private lateinit var musicPathEditText: TextInputEditText
    private lateinit var saveButton: Button
    private lateinit var cancelButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        initViews()
        loadSettings()
        setupClickListeners()
    }

    private fun initViews() {
        deviceNameEditText = findViewById(R.id.deviceNameEditText)
        musicPathEditText = findViewById(R.id.musicPathEditText)
        saveButton = findViewById(R.id.saveButton)
        cancelButton = findViewById(R.id.cancelButton)
    }

    private fun loadSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        deviceNameEditText.setText(prefs.getString(KEY_DEVICE_NAME, "") ?: "")
        musicPathEditText.setText(prefs.getString(KEY_MUSIC_PATH, "") ?: "")
    }

    private fun setupClickListeners() {
        saveButton.setOnClickListener {
            saveSettings()
        }

        cancelButton.setOnClickListener {
            finish()
        }
    }

    private fun saveSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(KEY_DEVICE_NAME, deviceNameEditText.text?.toString()?.trim() ?: "")
            .putString(KEY_MUSIC_PATH, musicPathEditText.text?.toString()?.trim() ?: "")
            .apply()

        Toast.makeText(this, R.string.settings_saved, Toast.LENGTH_SHORT).show()
        
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK
        startActivity(intent)
        finish()
    }
}