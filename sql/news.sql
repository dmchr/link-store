/*
 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 50529
 Source Host           : localhost
 Source Database       : news

 Target Server Type    : MySQL
 Target Server Version : 50529
 File Encoding         : utf-8

 Date: 04/07/2013 17:00:08 PM
*/

SET NAMES utf8;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
--  Table structure for `likes`
-- ----------------------------
DROP TABLE IF EXISTS `likes`;
CREATE TABLE `likes` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `news_id` int(10) unsigned NOT NULL,
  `is_liked` tinyint(1) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `news_id` (`news_id`),
  CONSTRAINT `likes_news_id` FOREIGN KEY (`news_id`) REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `news`
-- ----------------------------
DROP TABLE IF EXISTS `news`;
CREATE TABLE `news` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `source_id` int(10) unsigned NOT NULL,
  `url` varchar(1024) NOT NULL,
  `title` varchar(1024) NOT NULL,
  `description` text NOT NULL,
  `published` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `source_id` (`source_id`),
  CONSTRAINT `news_source_id` FOREIGN KEY (`source_id`) REFERENCES `source` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `reads`
-- ----------------------------
DROP TABLE IF EXISTS `reads`;
CREATE TABLE `reads` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `news_id` int(10) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `news_id` (`news_id`),
  CONSTRAINT `reads_news_id` FOREIGN KEY (`news_id`) REFERENCES `news` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `source`
-- ----------------------------
DROP TABLE IF EXISTS `source`;
CREATE TABLE `source` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(512) NOT NULL,
  `url` varchar(1024) NOT NULL,
  `is_active` tinyint(1) unsigned NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

-- ----------------------------
--  Records of `source`
-- ----------------------------
BEGIN;
INSERT INTO `source` VALUES ('1', 'Хабрахабр / Лучшие за сутки / Посты', 'http://habrahabr.ru/rss/best/', '1'), ('2', 'Slender Means', 'http://slendrmeans.wordpress.com/feed/', '1'), ('3', 'Wes McKinney\'s Blog', 'http://wesmckinney.com/blog/?feed=rss2', '1'), ('4', 'Joel on Software', 'http://joelonsoftware.com/rss.xml', '1'), ('5', 'Greg Reda', 'http://www.gregreda.com/feeds/all.atom.xml', '1'), ('6', 'Marco.org', 'http://www.marco.org/rss', '1');
COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
