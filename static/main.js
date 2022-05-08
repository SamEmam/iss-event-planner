function hiddenText(buttonID, divID) {
  var button = document.getElementById(buttonID);
  var div = document.getElementById(divID);
  if (div.style.display === "none") {
    div.style.display = "block";
    button.remove()
  } else {
    div.style.display = "none";
  }
}








