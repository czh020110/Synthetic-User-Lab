"""测试自托管测试产品站点 ShopLab 的页面可访问性与 UX 摩擦点埋点。"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_test_site_pages_accessible():
    """测试站点 4 个页面均可通过 /site/ 挂载点访问。"""
    for page in ["/site/", "/site/index.html", "/site/product.html", "/site/checkout.html", "/site/success.html"]:
        resp = client.get(page)
        assert resp.status_code == 200, f"{page} 返回 {resp.status_code}"


def test_index_page_has_product_entry():
    """首页包含可点击的商品详情入口。"""
    resp = client.get("/site/index.html")
    assert "查看详情" in resp.text
    assert "product.html" in resp.text


def test_product_page_has_coupon_friction():
    """商品页埋入摩擦点 1：优惠券错误提示模糊。"""
    resp = client.get("/site/product.html")
    # 优惠券输入框存在
    assert "coupon-input" in resp.text
    # 模糊错误提示文案埋点
    assert "操作失败，请重试" in resp.text


def test_checkout_page_has_hidden_fee_friction():
    """结算页埋入摩擦点 2：默认勾选加急配送，运费默认计入总价。"""
    resp = client.get("/site/checkout.html")
    # 精确匹配 ship-express 输入的 checked 属性，避免误匹配 JS 里的 .checked。
    assert 'data-testid="ship-express" checked' in resp.text
    # 运费行与默认总价 ¥924
    assert "shipping-fee" in resp.text
    assert "¥924" in resp.text


def test_checkout_page_has_vague_error_friction():
    """结算页埋入摩擦点 3：表单校验失败时错误提示模糊。"""
    resp = client.get("/site/checkout.html")
    assert "出错了，请检查后重试" in resp.text
    assert "error-box" in resp.text


def test_checkout_page_has_verify_code_friction():
    """结算页埋入摩擦点 4：验证码提示埋在页面底部，需滚动可见，且远离输入框。"""
    resp = client.get("/site/checkout.html")
    assert "verify-code" in resp.text
    assert "verify-hint" in resp.text
    assert "8204" in resp.text


def test_success_page_has_order_info():
    """成功页显示订单号与支付金额，作为成功判定依据。"""
    resp = client.get("/site/success.html")
    assert "支付成功" in resp.text
    assert "order-id" in resp.text
    assert "paid-amount" in resp.text
