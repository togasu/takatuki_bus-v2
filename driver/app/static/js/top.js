// Driver Service Frontend JavaScript

$(document).ready(function() {
    // ハンバーガーメニューの動作
    $('#js-hamburger').click(function() {
        $(this).toggleClass('active');
        $('#js-nav').toggleClass('active');
    });

    // 日時の更新
    function updateDateTime() {
        const now = new Date();
        const date = now.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });
        const time = now.toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        $('#date').text(date);
        $('#time').text(time);
    }

    // 初期化とインターバル設定
    updateDateTime();
    setInterval(updateDateTime, 1000);

    // バス運行状況の取得（模擬データ）
    function fetchBusStatus() {
        // 実際の実装では、APIエンドポイントからデータを取得
        const mockData = {
            nextBus: "15:30発 - 大学前行き",
            followingBus: "16:00発 - 駅前行き",
            status: "正常運行"
        };

        if ($('#next-bus').length) {
            $('#next-bus').text(mockData.nextBus);
        }
        if ($('#following-bus').length) {
            $('#following-bus').text(mockData.followingBus);
        }
        if ($('#bus-status').length) {
            $('#bus-status').text(mockData.status);
        }
    }

    // 初期データ読み込み
    fetchBusStatus();

    // 5分ごとにバス状況を更新
    setInterval(fetchBusStatus, 300000);

    // WebSocket接続（Socket.IO）
    if (typeof io !== 'undefined') {
        const socket = io();

        socket.on('connect', function() {
            console.log('WebSocket接続が確立されました');
        });

        socket.on('bus_update', function(data) {
            console.log('バス情報の更新を受信:', data);
            // バス情報の更新処理
            if (data.nextBus && $('#next-bus').length) {
                $('#next-bus').text(data.nextBus);
            }
            if (data.followingBus && $('#following-bus').length) {
                $('#following-bus').text(data.followingBus);
            }
        });

        socket.on('disconnect', function() {
            console.log('WebSocket接続が切断されました');
        });
    }

    // エラーハンドリング
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        console.error('AJAX エラー:', thrownError);
        if ($('.error-message').length === 0) {
            $('main').prepend('<div class="error-message">通信エラーが発生しました。ページを更新してください。</div>');
        }
    });

    // ページ離脱時の確認
    $(window).on('beforeunload', function() {
        // 重要な処理中の場合のみ確認メッセージを表示
        if ($('.processing').length > 0) {
            return '処理中です。ページを離れてもよろしいですか？';
        }
    });
});

// ユーティリティ関数
function showLoading(element) {
    $(element).append('<span class="loading"></span>');
}

function hideLoading(element) {
    $(element).find('.loading').remove();
}

function showMessage(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-info';
    const messageHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('.main').prepend(messageHtml);
    
    // 5秒後に自動で非表示
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}