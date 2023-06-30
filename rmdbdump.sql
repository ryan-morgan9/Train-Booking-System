-- MySQL dump 10.13  Distrib 8.0.23, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: traindb
-- ------------------------------------------------------
-- Server version	8.0.23

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `trainbooking`
--

DROP TABLE IF EXISTS `trainbooking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trainbooking` (
  `bookId` int NOT NULL AUTO_INCREMENT,
  `userId` int DEFAULT NULL,
  `tripId` varchar(20) NOT NULL,
  `departDate` date NOT NULL,
  `returnDate` date DEFAULT NULL,
  `adultNum` int DEFAULT NULL,
  `childNum` int DEFAULT NULL,
  `tripType` varchar(20) DEFAULT NULL,
  `priceTotal` int DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`bookId`),
  UNIQUE KEY `bookId` (`bookId`),
  KEY `userId` (`userId`),
  KEY `tripId` (`tripId`),
  CONSTRAINT `trainbooking_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `user` (`userId`),
  CONSTRAINT `trainbooking_ibfk_2` FOREIGN KEY (`tripId`) REFERENCES `traintimetable` (`tripId`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainbooking`
--

LOCK TABLES `trainbooking` WRITE;
/*!40000 ALTER TABLE `trainbooking` DISABLE KEYS */;
INSERT INTO `trainbooking` VALUES (74,10,'1000','2021-05-17',NULL,1,0,'oneway',140,'2021-05-12 12:12:33'),(78,10,'1000','2021-05-14',NULL,1,1,'oneway',210,'2021-05-12 13:16:56');
/*!40000 ALTER TABLE `trainbooking` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `traintimetable`
--

DROP TABLE IF EXISTS `traintimetable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traintimetable` (
  `tripId` varchar(40) NOT NULL,
  `departPlace` varchar(40) NOT NULL,
  `departTime` time NOT NULL,
  `arrivePlace` varchar(40) NOT NULL,
  `arriveTime` time NOT NULL,
  `price` int DEFAULT NULL,
  PRIMARY KEY (`tripId`),
  UNIQUE KEY `tripId` (`tripId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `traintimetable`
--

LOCK TABLES `traintimetable` WRITE;
/*!40000 ALTER TABLE `traintimetable` DISABLE KEYS */;
INSERT INTO `traintimetable` VALUES ('1000','Newcastle','16:45:00','Bristol','23:00:00',140),('1001','Bristol','08:00:00','Newcastle','14:15:00',140),('1002','Cardiff','06:00:00','Edinburgh','13:30:00',120),('1003','Edinburgh','18:30:00','Cardiff','01:00:00',120),('1004','Bristol','11:30:00','Manchester','16:30:00',100),('1005','Manchester','12:20:00','Bristol','17:20:00',100),('1006','Bristol','07:40:00','London','11:00:00',100),('1007','London','11:00:00','Manchester','17:40:00',130),('1008','Manchester','12:20:00','Glasgow','18:10:00',130),('1009','Bristol','07:40:00','Glasgow','13:05:00',160),('1010','Glasgow','14:30:00','Newcastle','20:45:00',130),('1011','Newcastle','16:15:00','Manchester','20:25:00',130),('1012','Manchester','18:25:00','Bristol','23:50:00',130),('1013','Bristol','06:20:00','Manchester','11:20:00',130),('1014','Portsmouth','12:00:00','Dundee','22:00:00',180),('1015','Dundee','10:00:00','Portsmouth','20:00:00',180),('1016','Southampton','12:00:00','Manchester','19:30:00',100),('1017','Manchester','19:00:00','Southampton','01:30:00',100),('1018','Birmingham','16:00:00','Newcastle','23:30:00',130),('1019','Newcastle','06:00:00','Brimingham','13:30:00',130),('1020','Aberdeen','07:00:00','Portsmouth','17:00:00',130),('1021','Bristol','14:00:00','Bournemouth','20:15:00',120);
/*!40000 ALTER TABLE `traintimetable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `userId` int NOT NULL AUTO_INCREMENT,
  `email` varchar(40) NOT NULL,
  `name` varchar(40) NOT NULL,
  `password` varchar(110) NOT NULL,
  `usertype` varchar(10) NOT NULL,
  PRIMARY KEY (`userId`),
  UNIQUE KEY `userId` (`userId`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (10,'ryan@email.com','Ryan','pbkdf2:sha256:150000$k17vuLa0$8252d6e49d04df0423725904fe47704e4d71e0da7d97d5256c5b2f40475f6829','admin'),(11,'elizabeth@email.com','Elizabeth','pbkdf2:sha256:150000$xeVfTdCj$4ea37276b709b846e013c814c804433dcccb36ebc51578f5234477556d25d889','customer');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-05-13 10:20:29
