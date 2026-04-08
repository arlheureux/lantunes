package com.lantunes.lantunes.api

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "lantunes_prefs")

class ApiClient(private val context: Context) {
    
    companion object {
        private var instance: ApiClient? = null
        private var baseUrl: String = "http://192.168.0.85:8080"
        
        fun getInstance(context: Context): ApiClient {
            if (instance == null) {
                instance = ApiClient(context)
            }
            return instance!!
        }
        
        fun setBaseUrl(url: String) {
            baseUrl = if (url.endsWith("/")) url.dropLast(1) else url
            instance = null // Reset to rebuild with new URL
        }
    }
    
    private val tokenKey = stringPreferencesKey("access_token")
    private val userKey = stringPreferencesKey("user_json")
    private val serverUrlKey = stringPreferencesKey("server_url")
    
    val tokenFlow: Flow<String?> = context.dataStore.data.map { it[tokenKey] }
    val userFlow: Flow<String?> = context.dataStore.data.map { it[userKey] }
    val serverUrlFlow: Flow<String?> = context.dataStore.data.map { it[serverUrlKey] }
    
    suspend fun getToken(): String? = context.dataStore.data.first()[tokenKey]
    suspend fun getServerUrl(): String? = context.dataStore.data.first()[serverUrlKey]
    
    private val authInterceptor = Interceptor { chain ->
        val token = runCatching { 
            context.dataStore.data.first()[tokenKey] 
        }.getOrNull()
        
        val request = if (token != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }
        chain.proceed(request)
    }
    
    private val client = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl("$baseUrl/")
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val api: LanTunesApi = retrofit.create(LanTunesApi::class.java)
    
    suspend fun saveToken(token: String) {
        context.dataStore.edit { it[tokenKey] = token }
    }
    
    suspend fun saveUser(userJson: String) {
        context.dataStore.edit { it[userKey] = userJson }
    }
    
    suspend fun saveServerUrl(url: String) {
        context.dataStore.edit { it[serverUrlKey] = url }
        setBaseUrl(url)
    }
    
    suspend fun clearSession() {
        context.dataStore.edit { prefs ->
            prefs.remove(tokenKey)
            prefs.remove(userKey)
        }
    }
    
    fun getStreamUrl(trackId: Int): String = "$baseUrl/api/playback/stream/$trackId"
    
    fun getArtworkUrl(path: String?): String {
        if (path.isNullOrEmpty()) return ""
        if (path.startsWith("http")) return path
        return "$baseUrl$path"
    }
}