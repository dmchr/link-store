/*
 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 50529
 Source Host           : localhost
 Source Database       : linkstore

 Target Server Type    : MySQL
 Target Server Version : 50529
 File Encoding         : utf-8

 Date: 07/04/2013 01:53:56 AM
*/

SET NAMES utf8;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
--  Table structure for `articles`
-- ----------------------------
DROP TABLE IF EXISTS `articles`;
CREATE TABLE `articles` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `url` varchar(1024) NOT NULL,
  `title` varchar(1024) DEFAULT NULL,
  `description` text,
  `published` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_articles-url` (`url`(255)) USING BTREE,
  KEY `idx-articles-published` (`published`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `articles_locations`
-- ----------------------------
DROP TABLE IF EXISTS `articles_locations`;
CREATE TABLE `articles_locations` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_article_id` int(11) unsigned NOT NULL,
  `location_type` enum('article','browser','source') NOT NULL,
  `location` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx-articles_locations-user_article_id` (`user_article_id`) USING BTREE,
  CONSTRAINT `fk-articles_locations-user_article_id` FOREIGN KEY (`user_article_id`) REFERENCES `user_articles` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `sources`
-- ----------------------------
DROP TABLE IF EXISTS `sources`;
CREATE TABLE `sources` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `type` enum('feed','twitter') NOT NULL DEFAULT 'feed',
  `title` varchar(512) NOT NULL DEFAULT 'No title',
  `url` varchar(1024) NOT NULL,
  `last_update` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `user_articles`
-- ----------------------------
DROP TABLE IF EXISTS `user_articles`;
CREATE TABLE `user_articles` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `article_id` int(11) unsigned NOT NULL,
  `rating` tinyint(2) unsigned DEFAULT '0',
  `is_read` tinyint(3) NOT NULL DEFAULT '0',
  `read_time` timestamp NULL DEFAULT NULL,
  `is_liked` tinyint(3) NOT NULL DEFAULT '0',
  `like_time` timestamp NULL DEFAULT NULL,
  `source_count` tinyint(3) unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq-user_articles` (`user_id`,`article_id`) USING BTREE,
  KEY `idx-user_article-user_id` (`user_id`) USING BTREE,
  KEY `idx-user_article-article_id` (`article_id`) USING BTREE,
  KEY `idx-user_articles-rating` (`rating`) USING BTREE,
  CONSTRAINT `fk-users_articles-article_id` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk-users_articles-user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `user_opml`
-- ----------------------------
DROP TABLE IF EXISTS `user_opml`;
CREATE TABLE `user_opml` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned DEFAULT NULL,
  `opml` text,
  `is_handled` tinyint(4) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx-user_opml-user_id` (`user_id`) USING BTREE,
  CONSTRAINT `fk-user_opml-user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `user_sources`
-- ----------------------------
DROP TABLE IF EXISTS `user_sources`;
CREATE TABLE `user_sources` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `source_id` int(11) unsigned NOT NULL,
  `is_active` tinyint(1) unsigned NOT NULL DEFAULT '1',
  `read_count` int(11) NOT NULL DEFAULT '0',
  `like_count` int(11) NOT NULL DEFAULT '0',
  `category` varchar(64) NOT NULL DEFAULT 'No category',
  PRIMARY KEY (`id`),
  KEY `idx-users_sources-user_id` (`user_id`) USING BTREE,
  KEY `idx-users_sources-source_id` (`source_id`) USING BTREE,
  KEY `idx-users_sources-is_active` (`is_active`) USING BTREE,
  KEY `idx-user_sources-user_id-source_id` (`user_id`,`source_id`) USING BTREE,
  KEY `idx-user_sources-read_count-like_count` (`is_active`,`read_count`,`like_count`) USING BTREE,
  CONSTRAINT `fk-users_sources-source_id` FOREIGN KEY (`source_id`) REFERENCES `sources` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk-users_sources-user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `users`
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Records of `users`
-- ----------------------------
BEGIN;
INSERT INTO `users` VALUES ('1', 'Test');
COMMIT;


SET FOREIGN_KEY_CHECKS = 1;
