"""Safe, actionable error messages without exposing provider payloads or secrets."""


def describe_error(exc: Exception) -> dict:
    kind = type(exc).__name__
    status = getattr(exc, "status_code", None)
    if kind == "APITimeoutError":
        message = "xkiro phản hồi quá lâu. Hãy thử lại sau hoặc chọn model khác trong .env."
    elif kind == "APIConnectionError":
        message = (
            "Không kết nối được tới xkiro. Hãy kiểm tra mạng, VPN/proxy hoặc tường lửa, "
            "và XKIRO_BASE_URL trong .env. Lỗi này chưa cho biết API key có hợp lệ hay không. "
            "Khi kết nối ổn định, gửi lại yêu cầu."
        )
    elif status == 401:
        message = "xkiro từ chối xác thực. Kiểm tra XKIRO_API_KEY trong .env."
    elif status == 402:
        message = "xkiro báo thiếu credit. Kiểm tra số dư hoặc quyền sử dụng model của tài khoản."
    elif status == 403:
        message = "xkiro từ chối truy cập. Kiểm tra quyền API, quyền dùng model hoặc giới hạn truy cập mạng."
    elif status == 404:
        message = "Không tìm thấy model hoặc endpoint. Kiểm tra XKIRO_MODEL và XKIRO_BASE_URL trong .env."
    elif status == 409:
        message = "xkiro báo yêu cầu trùng đang được xử lý. Chờ một lúc rồi gửi lại."
    elif status == 429:
        message = "xkiro đang giới hạn số yêu cầu. Chờ một lúc rồi thử lại."
    elif isinstance(status, int) and status >= 500:
        message = "Dịch vụ xkiro đang gặp lỗi. Hãy thử lại sau."
    else:
        message = "Chưa xử lý được yêu cầu. Xem mã lỗi bên dưới để chẩn đoán; thử lại hoặc kiểm tra cấu hình model."
    return {"error_type": kind, "http_status": status, "assistant_text": message}
