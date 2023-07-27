/* GLOBAL FUNCTIONS */
function ExecPythonCommand(pythonCommand){
    var request = new XMLHttpRequest()
    request.open("GET", "/" + pythonCommand, true)
    request.send()
}


/* SIGNIN/SIGNUP FUNCTIONS */
let switchCtn = document.querySelector("#switch-cnt");
let switchC1 = document.querySelector("#switch-c1");
let switchC2 = document.querySelector("#switch-c2");
let switchCircle = document.querySelectorAll(".switch__circle");
let switchBtn = document.querySelectorAll(".switch-btn");
let aContainer = document.querySelector("#a-container");
let bContainer = document.querySelector("#b-container");
let allButtons = document.querySelectorAll(".submit");

let changeForm = e => {

    switchCtn.classList.add("is-gx");

    switchCtn.classList.toggle("is-txr");
    switchCircle[0].classList.toggle("is-txr");
    switchCircle[1].classList.toggle("is-txr");

    switchC1.classList.toggle("is-hidden");
    switchC2.classList.toggle("is-hidden");
    aContainer.classList.toggle("is-txl");
    bContainer.classList.toggle("is-txl");
    bContainer.classList.toggle("is-z200");
};

let mainF = e => {
    document.getElementsByClassName('submit')[0].addEventListener("click", () => {
        document.getElementById('a-form').submit();
    });
    document.getElementsByClassName('submit')[0].addEventListener("click", () => {
        document.getElementById('b-form').submit();
    });

    for (var i = 0; i < switchBtn.length; i++) {
        switchBtn[i].addEventListener("click", changeForm);
    }
};

window.addEventListener("load", mainF);


/* LOADING ANIMATION */
document.onreadystatechange = function () {
    if (document.readyState !== "complete") {
        document.querySelector(
            "body").style.visibility = "hidden";
        document.querySelector(
            "#gooey").style.visibility = "visible";
    } else {
        document.querySelector(
            "#gooey").style.display = "none";
        document.querySelector(
            "body").style.visibility = "visible";
    }
};


/* ADDING SUGGESTION TO USERNAME INPUT */
let suggestion_boxes = document.querySelectorAll('.suggestion__text');
let uname_inp_box = document.getElementById('r-uname');
let random_button = document.querySelector('#random-suggestion-btn');
const username_list = {{USERNAME_LIST | to_json}};
var ind = 0;

Array.from(suggestion_boxes).forEach(el => {
    el.addEventListener('click', () => {
        uname_inp_box.value = el.textContent;
    });
});

random_button.addEventListener('click', () => {
    if (ind > 54)
        ind = 0;
    for(var i=0; i<6; i++) {
        suggestion_boxes[i].innerHTML = username_list[ind + i];
    }
    ind += 6;
})
random_button.click();


/* CYCLE NAVIGATION PANE */
var nav_pane = document.getElementsByClassName('nav-pane');
var nav_items = document.getElementsByClassName("nav-item");
var current_pane = nav_items[0];
for (var i = 0, len = nav_pane.length; i < len; i++) {
    (function (index) {
        nav_pane[i].onclick = function () {
            current_pane.classList.add("disabled");
            current_pane = nav_items[index];
            current_pane.classList.remove("disabled");
        };
    })(i);
}