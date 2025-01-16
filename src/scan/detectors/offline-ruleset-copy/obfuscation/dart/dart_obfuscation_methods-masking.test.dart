// TP
var result = 'hello'.substring(1).substring(2).substring(3);
var replaced = 'hello world'.replaceAll('o', '0').replaceAll('l', '1').replaceAll('e', '3');
var split = 'apple,banana,orange'.split(',').split(',').split(',');
var joined = ['apple', 'banana', 'cherry'].join(", ").join(" - ").join(": ");
var codeUnit = 'hello'.codeUnitAt(0).codeUnitAt(1).codeUnitAt(2);

// FP
var result = 'hello'.substring(1).substring(2);
var replaced = 'hello world'.replaceAll('o', '0').replaceAll('l', '1');
var split = 'apple,banana,orange'.split(',');
var joined = ['apple', 'banana'].join(", ");
var codeUnit = 'hello'.codeUnitAt(0);