# V2ray-fpm






<p align="center">
  <img src="https://github.com/massooti/V2ray-fpm/blob/main/images/woman-life-freedom.png" alt="woman, life, freedom" /><br>
	<i>woman, life, freedom</i><br>
	<i>The use of the slogan "Woman, Life, Freedom" has become a symbol of the protests in Iran, and this application aims to providing a way for people to connect to free internet.</i>
</p>

# GUI web application for V2ray client users:

**This project is a web-based graphical user interface (GUI) for the V2Ray client using the VMess protocol. It provides an easy-to-use interface for configuring and connecting to V2Ray servers.**


## Prerequisites
* Docker and docker-compose installed on the host machine.
* A V2Ray server running with the VMess protocol enabled.


## Installation and Usage

Clone this repository to your local machine:
```
git clone https://github.com/massooti/V2ray-fpm.git
```
Navigate to the project directory:
```
cd V2ray-fpm
```
You can install it on your local machine simply by running ``` ./install.sh ``` or via docker.

Start the containers using docker-compose:
```
docker-compose up -d
```
Open your web browser and navigate to http://localhost:8000 to access the web interface.

Enter the V2Ray server connection details in the web interface, and click "Connect".

You should now be connected to the V2Ray server.

## Screenshots
### For see screenshots click [images](https://github.com/massooti/V2ray-fpm/tree/main/images)

## Acknowledgments

**This project was inspired by the [multi-v2ray](https://github.com/Jrohy/multi-v2ray).**
