var readme_url = "https://raw.githubusercontent.com/imageio/imageio/master/README.md";

var xhr = new XMLHttpRequest();
xhr.open('GET', readme_url, true);
xhr.responseType = 'text';

xhr.onreadystatechange = function (event) {
    if (this.readyState === 4 && this.status === 200) {
        document.getElementById("content").innerHTML = this.responseText
    }
};

function load_content_from_readme() {
  document.getElementById("content").innerHTML = "loading ..."
  xhr.send();
}
