from lanzou.api._internal.parsers import (
    parse_file_page_context,
    parse_folder_page_context,
    parse_password_share_ajax,
    resolve_iframe_url,
    resolve_sign_from_iframe,
)
from lanzou.api.utils import remove_notes


def test_parse_file_page_context():
    context = parse_file_page_context("<html>ok</html>", "https://sub.lanzoux.com/iabc123", "https://sub.lanzoux.com/iabc123")
    assert context["origin"] == "https://sub.lanzoux.com"
    assert context["ajax_url"] == "https://sub.lanzoux.com/ajaxm.php"
    assert context["referer"] == "https://sub.lanzoux.com/iabc123"


def test_parse_folder_page_context():
    html = """
    <script>
    var abcdef = '1234567890';
    var ghijkl = 'abcdefghijklmnop';
    </script>
    'lx':2,
    'fid':'7654321',
    <div class="user-title">Folder Name</div>
    <span id="filename">desc text</span>
    """
    context = parse_folder_page_context(html, "https://foo.lanzoux.com/b1234567", "https://foo.lanzoux.com/b1234567")
    assert context["origin"] == "https://foo.lanzoux.com"
    assert context["ajax_url"] == "https://foo.lanzoux.com/filemoreajax.php"
    assert context["lx"] == "2"
    assert context["t"] == "1234567890"
    assert context["k"] == "abcdefghijklmnop"
    assert context["folder_id"] == "7654321"
    assert context["folder_name"] == "Folder Name"
    assert context["folder_desc"] == "desc text"


def test_parse_folder_page_context_from_ajax_block():
    html = """
    <span id="filename">desc text</span>
    <div class="rets">05-07<a href="#">举报</a></div>
    <script>
    var ing1dl = 'Folder Ajax Name';
    document.title = ing1dl;
    var ibjd9z = '1778126216';
    var _hhpbs = 'b9302ccf493315fe56face04fe20a3ef';
    function file(){
        $.ajax({
            type : 'post',
            url : '/filemoreajax.php?file=13469945',
            data : {
                'lx':2,
                'fid':13469945,
                'uid':'1113624',
                'pg':pgs,
                'rep':'0',
                't':ibjd9z,
                'k':_hhpbs,
                'up':1,
                'ls':1,
                'pwd':pwd
            },
            dataType : 'json'
        })
    }
    </script>
    """
    context = parse_folder_page_context(html, "https://foo.lanzoux.com/b1234567", "https://foo.lanzoux.com/b1234567")
    assert context["ajax_url"] == "https://foo.lanzoux.com/filemoreajax.php?file=13469945"
    assert context["lx"] == "2"
    assert context["folder_id"] == "13469945"
    assert context["uid"] == "1113624"
    assert context["rep"] == "0"
    assert context["up"] == "1"
    assert context["ls"] == "1"
    assert context["t"] == "1778126216"
    assert context["k"] == "b9302ccf493315fe56face04fe20a3ef"
    assert context["folder_name"] == "Folder Ajax Name"
    assert context["folder_desc"] == "desc text"


def test_resolve_iframe_url():
    context = {"origin": "https://foo.lanzoux.com"}
    assert resolve_iframe_url(context, "/fn?abc") == "https://foo.lanzoux.com/fn?abc"


def test_resolve_sign_from_iframe_direct():
    frame_html = "'sign':'ABCDEFGHIJKLMNOPQRST',"
    assert resolve_sign_from_iframe(frame_html) == "ABCDEFGHIJKLMNOPQRST"


def test_resolve_sign_from_iframe_variable():
    frame_html = "'sign':abc123,\nvar abc123 = 'ABCDEFGHIJKLMNOPQRST';"
    assert resolve_sign_from_iframe(frame_html) == "ABCDEFGHIJKLMNOPQRST"


def test_parse_password_share_ajax_ignores_block_comments():
    html = """
    /*
    $.ajax({
      type : 'post',
      url : '/ajaxm.php?file=111',
      data : { 'action':'downprocess','sign':'OLD_SIGN','kd':kdns,'p':pwd },
      dataType : 'json'
    })
    */
    var kdns = 1;
    $.ajax({
      type : 'post',
      url : '/ajaxm.php?file=222',
      data : { 'action':'downprocess','sign':'NEW_SIGN','kd':kdns,'p':pwd },
      dataType : 'json'
    })
    """
    info = parse_password_share_ajax(remove_notes(html))
    assert info["ajax_path"] == "/ajaxm.php?file=222"
    assert info["sign"] == "NEW_SIGN"
    assert info["kd"] == "1"
