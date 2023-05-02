//
// Copyright © 2021 Brewing Notes https://brewingnotes.ru
//
// Updated Date: 01.01.2021
// Author: joss

const colorSRM = {0:'#fff4d4',1:'#ffe699',2:'#ffd878',3:'#ffca5A',4:'#ffbf42',5:'#fbb123',6:'#f8a600',7:'#f39c00',8:'#eA8f00',9:'#e58500',10:'#de7C00',11:'#d77200',12:'#cf6900',13:'#cb6200',14:'#c35900',15:'#bb5100',16:'#b54c00',17:'#b04500',18:'#a63e00',19:'#a13700',20:'#9d3200',21:'#952d00',22:'#8e2900',23:'#882300',24:'#821e00',25:'#7b1a00',26:'#771900',27:'#701400',28:'#6a0e00',29:'#660d00',30:'#5e0b00',31:'#5a0a02',32:'#600903',33:'#520907',34:'#4c0505',35:'#470606',36:'#420607',37:'#3d0708',38:'#370607',39:'#2d0607',40:'#1f0506',41:'#000000'};
const hydrometerFactor = {15:0.0006,16:0.0005,17:0.0004,18:0.0003,19:0.000,20:0,21:0.0002,22:0.0003,23:0.0005,24:0.0007,25:0.0009,26:0.0011,27:0.0013,28:0.0016,29:0.0018,30:0.0021};
const pitchRateAle = {'light': 6, 'medium': 12, 'high': 18};
const pitchRateLager = {'light': 12, 'medium': 18, 'high': 24};
const levelGravity = {'light': 15, 'high': 19};
function round(a, b) {
	return Number(Math.round(a+'e'+b)+'e-'+b);
}
function convertPtG(p) {
	return (p / (258.6 - ((p / 258.2) * 227.1))) + 1;
}
function convertGtP(g) {
	return (-1 * 616.868) + (1111.14 * g) - (630.272 * Math.pow(g, 2)) + (135.997 * Math.pow(g, 3));
}
function calcAlcoOld(og, fg) {
	return (og - fg) * 131.25;
}
function calcAlcoNew(og, fg) {
	return (76.08 * (og - fg) / (1.775 - og)) * (fg / 0.794);
}
function convertEBCToSRM(e) {
	return e / 1.97;
}
function convertSRMToEBC(s) {
	return s * 1.97;
}
function convertSRMToLovibond(s) {
	return (s + 0.76) / 1.3546;
}
function convertLovibondToSRM(l) {
	return (1.3546 * l) - 0.76;
}
function convertLovibondToEBC(l) {
	return ((1.3546 * l) - 0.76) * 1.97;
}
function convertEBCToLovibond(e) {
	return (e / 1.97 + 0.76) / 1.3546;
}
function convertGramsToOunces(grams) {
	return 0.0352739619 * grams;
}
function convertOuncesToGrams(ounces) {
	return 28.3495231648 * ounces;
}
function convertLitersToGallons(liters) {
	return 0.264172052 * liters;
}
function convertGallonsToLiters(gallons) {
	return 3.785405083 * gallons;
}
function convertCelsiusToFahrenheit(c) {
	return 1.8 * c + 32;
}
function convertFahrenheitToCelsius(f) {
	return (f - 32) / 1.8;
}
function convertPlato(a, b) {
		let sg = Number($('input[name='+a+']').val().replace(',', '.'));
		let pl = convertGtP(sg);
		$('input[name='+b+']').val(round(pl, 1));
}
function convertSG(a, b) {
		let pl = Number($('input[name='+a+']').val().replace(',', '.'));
		let sg = convertPtG(pl);
		$('input[name='+b+']').val(round(sg, 3));
}
function IBUOG(ibu, og) {
          return ibu / ((og - 1) * 1000);
}
