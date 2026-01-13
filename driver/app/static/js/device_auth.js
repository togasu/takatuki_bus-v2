/**
 * デバイスフィンガープリント生成とMACアドレス風ID取得
 * 
 * 注意: ブラウザからは実際のMACアドレスを取得できないため、
 * デバイス固有の情報からハッシュを生成してMACアドレス風のIDを作成します。
 */

(function() {
    'use strict';
    
    /**
     * Canvas Fingerprintを生成
     */
    function getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.textBaseline = 'alphabetic';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('Device Fingerprint 🚌', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Device Fingerprint 🚌', 4, 17);
            
            return canvas.toDataURL();
        } catch (e) {
            console.error('Canvas fingerprint error:', e);
            return '';
        }
    }
    
    /**
     * WebGLの情報を取得
     */
    function getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) return '';
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (!debugInfo) return '';
            
            return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        } catch (e) {
            console.error('WebGL info error:', e);
            return '';
        }
    }
    
    /**
     * デバイス情報を収集
     */
    function collectDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages ? navigator.languages.join(',') : '',
            platform: navigator.platform,
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            deviceMemory: navigator.deviceMemory || 0,
            screenResolution: `${screen.width}x${screen.height}`,
            screenColorDepth: screen.colorDepth,
            screenPixelDepth: screen.pixelDepth,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            canvasFingerprint: getCanvasFingerprint(),
            webglInfo: getWebGLInfo(),
            touchSupport: 'ontouchstart' in window,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack || 'unspecified'
        };
    }
    
    /**
     * 文字列をSHA-256ハッシュ化
     */
    async function sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }
    
    /**
     * デバイスIDを生成（MACアドレス風の形式）
     */
    async function generateDeviceId() {
        try {
            const deviceInfo = collectDeviceInfo();
            const infoString = JSON.stringify(deviceInfo);
            const hash = await sha256(infoString);
            
            // 最初の12文字を使用してMACアドレス風の形式に変換
            const macLike = hash.substring(0, 12)
                .match(/.{1,2}/g)
                .join(':')
                .toUpperCase();
            
            console.log('[Device ID] Generated:', macLike);
            return macLike;
            
        } catch (error) {
            console.error('[Device ID] Generation failed:', error);
            
            // フォールバック: ランダムなMACアドレス風IDを生成
            const randomMac = Array.from({ length: 6 }, () => 
                Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
            ).join(':').toUpperCase();
            
            console.warn('[Device ID] Using fallback:', randomMac);
            return randomMac;
        }
    }
    
    /**
     * デバイスIDをローカルストレージに保存/取得
     */
    async function getOrCreateDeviceId() {
        const storageKey = 'driver_device_id';
        
        // 既存のIDをチェック
        let deviceId = localStorage.getItem(storageKey);
        
        if (deviceId) {
            console.log('[Device ID] Existing ID found:', deviceId);
            return deviceId;
        }
        
        // 新しいIDを生成
        deviceId = await generateDeviceId();
        
        try {
            localStorage.setItem(storageKey, deviceId);
            console.log('[Device ID] New ID stored:', deviceId);
        } catch (e) {
            console.warn('[Device ID] Could not store in localStorage:', e);
        }
        
        return deviceId;
    }
    
    /**
     * すべてのfetchリクエストにデバイスIDヘッダーを追加
     */
    async function setupDeviceIdHeader() {
        const deviceId = await getOrCreateDeviceId();
        
        // fetchのインターセプト
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            // リクエストオプションにヘッダーを追加
            if (args[1]) {
                args[1].headers = {
                    ...args[1].headers,
                    'X-Client-MAC': deviceId
                };
            } else {
                args[1] = {
                    headers: {
                        'X-Client-MAC': deviceId
                    }
                };
            }
            
            return originalFetch.apply(this, args);
        };
        
        console.log('[Device ID] Header setup complete');
    }
    
    /**
     * フォーム送信時にデバイスIDを追加
     */
    async function setupFormDeviceId() {
        const deviceId = await getOrCreateDeviceId();
        
        // すべてのフォームにhiddenフィールドを追加
        document.querySelectorAll('form').forEach(form => {
            // 既存のhiddenフィールドをチェック
            let hiddenField = form.querySelector('input[name="device_mac"]');
            
            if (!hiddenField) {
                hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'device_mac';
                form.appendChild(hiddenField);
            }
            
            hiddenField.value = deviceId;
        });
        
        console.log('[Device ID] Form fields setup complete');
    }
    
    /**
     * デバイスIDを表示（デバッグ用）
     */
    async function displayDeviceId() {
        const deviceId = await getOrCreateDeviceId();
        
        // デバッグ情報を表示
        if (window.location.search.includes('debug=true')) {
            const debugDiv = document.createElement('div');
            debugDiv.style.cssText = `
                position: fixed;
                bottom: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                z-index: 10000;
            `;
            debugDiv.innerHTML = `
                <strong>Device ID:</strong><br>
                ${deviceId}<br>
                <small>このIDでデバイスを識別します</small>
            `;
            document.body.appendChild(debugDiv);
        }
    }
    
    /**
     * 初期化
     */
    async function init() {
        console.log('[Device ID] Initializing...');
        
        try {
            await setupDeviceIdHeader();
            await setupFormDeviceId();
            await displayDeviceId();
            
            console.log('[Device ID] Initialization complete');
        } catch (error) {
            console.error('[Device ID] Initialization failed:', error);
        }
    }
    
    // DOMContentLoadedで初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // グローバルに公開（必要に応じて）
    window.DeviceAuth = {
        getDeviceId: getOrCreateDeviceId,
        regenerateDeviceId: async function() {
            localStorage.removeItem('driver_device_id');
            return await getOrCreateDeviceId();
        }
    };
    
})();
