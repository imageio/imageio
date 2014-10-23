var readme_url = "../README.md";

var xhr = new XMLHttpRequest();
xhr.open('GET', readme_url, true);
xhr.responseType = 'text';

xhr.onreadystatechange = function (event) {
    if (this.readyState === 4 && this.status === 200) {
        document.getElementById("content").innerHTML = this.responseText
    }
};

function load_content_from_readme() {
  xhr.send();
}
